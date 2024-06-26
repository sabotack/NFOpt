import argparse
import os
import pandas as pd
import statistics as stats
import multiprocessing as mp

from multiprocessing import set_start_method

from nfopt.calc_type_enum import CalcType
from nfopt.utils import data as dataUtils
from nfopt.utils import network as nwUtils
from nfopt.utils import log
from nfopt.linear_optimization import netflow, optimizer as linOpt

logger = log.setupCustomLogger(__name__)

AVG_CAPACITY = int(os.getenv("AVERAGE_CAPACITY"))


def calcLinkUtil(links):
    util = {}

    for linkKey in links:
        util[linkKey] = (
            links[linkKey]["totalTraffic"] / links[linkKey]["capacity"] * 100
        )

    return util


def process_flows_hour(timestamp, flows, traffic, args, links):
    logger.info(f"Processing {timestamp} with {len(flows)} flows...")
    ratios = None
    useRatios = False

    # Read ratios if specified
    if args.use_ratios:
        hour = timestamp[4:6]
        day, ratioType, date = args.use_ratios
        useRatios = True
        ratios = dataUtils.readPathRatios(date, day, hour, ratioType)
    elif args.use_paths:
        hour = timestamp[4:6]
        day, date, useRatios = args.use_paths
        useRatios = useRatios == "True"
        ratios = dataUtils.readPathRatios(date, day, hour)
        i = 0
        for flow in flows:
            if flow not in ratios:
                continue
            i += 1
            flows[flow] = list(ratios[flow].keys())
        logger.info(f"Updated {i} flows with paths!")

    # Initialize totalTraffic and listFlows for all links
    for linkKey in links:
        links[linkKey]["totalTraffic"] = 0
        links[linkKey]["listFlows"] = []

    for flow in flows:
        # Get all links in the flow
        linksFlow = nwUtils.getLinksFromFlow(flows[flow])
        identicalPaths = True

        if ratios is not None:
            for path in flows[flow]:
                if flow not in ratios or path not in ratios[flow]:
                    identicalPaths = False
                    break

        # Update totalTraffic and listFlows for each link
        for link in linksFlow:
            if link not in links:
                sd = link.split(";")

                links[link] = {
                    "linkStart": sd[0],
                    "linkEnd": sd[1],
                    "capacity": AVG_CAPACITY,
                    "totalTraffic": 0,
                    "listFlows": [],
                }

            totalTraffic = 0
            for path in flows[flow]:
                if link in path:
                    if useRatios and identicalPaths:
                        totalTraffic += traffic[flow] * float(ratios[flow][path])
                    else:
                        totalTraffic += traffic[flow] * (1 / len(flows[flow]))
            links[link]["totalTraffic"] += totalTraffic
            links[link]["listFlows"].append(flow)

    # Run linear optimization or baseline calculations
    if args.model_type == CalcType.BASELINE.value:
        linkUtil = calcLinkUtil(links)
    elif args.model_type == CalcType.PATHS.value:
        netflow.optMC(args, links, traffic, timestamp)
        return None
    else:
        linkUtil = linOpt.runLinearOptimizationModel(
            args, links, flows, traffic, timestamp, args.save_lp_models
        )

    return [
        timestamp,
        min(linkUtil.values()),
        max(linkUtil.values()),
        stats.mean(linkUtil.values()),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "model_type",
        choices=[
            CalcType.BASELINE.value,
            CalcType.AVERAGE.value,
            CalcType.MAX.value,
            CalcType.SQUARED.value,
            CalcType.PATHS.value,
        ],
        help="type of calculation to run",
    )
    parser.add_argument(
        "day",
        type=int,
        nargs="?",
        default=2,
        help="day number of data to process",
    )
    parser.add_argument(
        "-slpm",
        "--save-lp-models",
        action="store_true",
        help="save linear optimization models",
    )
    parser.add_argument(
        "-ur",
        "--use-ratios",
        nargs=3,
        metavar=("DAY", "TYPE", "DATE"),
        help="use existing path ratios for calculations",
    )
    parser.add_argument(
        "-up",
        "--use-paths",
        nargs=3,
        metavar=("DAY", "DATE", "USERATIOS?"),
        help="use existing paths for calculations",
    )

    args = parser.parse_args()

    if args.use_ratios:
        day, ratioType, date = args.use_ratios
        if not day.isdigit():
            parser.error("Invalid day number.")
        if (
            not date.isdigit()
            or len(date) != 8
            or int(date[4:6]) > 12
            or int(date[6:]) > 31
        ):
            parser.error("Invalid date. Please use a date in the format YYYYMMDD.")
        if ratioType not in [
            CalcType.AVERAGE.value,
            CalcType.MAX.value,
            CalcType.SQUARED.value,
            CalcType.PATHS.value,
        ]:
            parser.error(
                "Invalid ratio type. Please use 'average', 'path', 'max' or 'squared'."
            )
        if args.model_type != CalcType.BASELINE.value:
            parser.error(
                "Cannot use existing path ratios with the specified model type."
            )

    if args.use_paths:
        day, date, useratios = args.use_paths
        if not day.isdigit():
            parser.error("Invalid day number.")
        if (
            not date.isdigit()
            or len(date) != 8
            or int(date[4:6]) > 12
            or int(date[6:]) > 31
        ):
            parser.error("Invalid date. Please use a date in the format YYYYMMDD.")
        if useratios not in ["True", "False"]:
            parser.error("Invalid useratios value. Please use 'True' or 'False'.")

    # Set start method to spawn to avoid issues with multiprocessing on Windows
    set_start_method("spawn")

    startTime = pd.Timestamp.now()
    logger.info("Started, model_type: " + str(args.model_type))

    flows = dataUtils.readFlows(args.day)
    links = dataUtils.readLinks()
    traffic = dataUtils.readTraffic(args.day)

    with mp.Pool(processes=dataUtils.CPU_THREADS) as pool:
        results = pool.starmap(
            process_flows_hour,
            [
                (timestamp, flows[timestamp], traffic[timestamp], args, links.copy())
                for timestamp in flows
            ],
        )

    if results is not None and results[0] is not None:
        results.sort()

        dataUtils.writeDataToFile(
            data=pd.DataFrame(
                results, columns=["timestamp", "min_util", "max_util", "avg_util"]
            ),
            parserArgs=args,
            outputFile="overviewData",
        )

    endTime = pd.Timestamp.now()

    # Log elapsed time in hours, minutes and seconds
    elapsedTime = (endTime - startTime).components
    logger.info(
        f"Finished, elapsed time: {elapsedTime.hours} hours, {elapsedTime.minutes} minutes, {elapsedTime.seconds} seconds"
    )
