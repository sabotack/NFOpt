import argparse
import pandas as pd
import statistics as stats
import multiprocessing as mp

from multiprocessing import set_start_method

from p6.calc_type_enum import CalcType
from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
from p6.linear_optimization import optimizer as linOpt

logger = log.setupCustomLogger(__name__)

DATA_DAY = 2


def calcLinkUtil(links):
    util = {}

    for linkKey in links:
        util[linkKey] = (
            links[linkKey]["totalTraffic"] / links[linkKey]["capacity"] * 100
        )

    return util


def process_flows_hour(timestamp, flows, traffic, args, linksCopy):
    links = linksCopy

    # Initialize totalTraffic and listFlows for all links
    for linkKey in links:
        links[linkKey]["totalTraffic"] = 0
        links[linkKey]["listFlows"] = []

    logger.info(f"Processing {timestamp} with {len(flows)} flows...")
    for flow in flows:
        routers = nwUtils.getRoutersHashFromFlow(flows[flow])
        flowLinks = nwUtils.getFlowLinks(routers, links)

        # Update links with traffic, and if link is new, add it to links
        for linkKey in flowLinks:
            if linkKey in links:
                links[linkKey]["totalTraffic"] += (
                    traffic[flow] * flowLinks[linkKey].trafficRatio
                )
            else:
                links[linkKey] = {
                    "linkStart": flowLinks[linkKey].linkStart,
                    "linkEnd": flowLinks[linkKey].linkEnd,
                    "capacity": flowLinks[linkKey].capacity,
                    "totalTraffic": traffic[flow] * flowLinks[linkKey].trafficRatio,
                    "listFlows": [],
                }

            # Add this flow to the list of flows for this link
            links[linkKey]["listFlows"].append(flow)

    # Run linear optimization or baseline calculations
    if args.model_type == CalcType.BASELINE.value:
        linkUtil = calcLinkUtil(links)
        return [
            timestamp,
            min(linkUtil.values()),
            max(linkUtil.values()),
            stats.mean(linkUtil.values()),
        ]
    else:
        avgLinkUtil, minLinkUtil, maxLinkUtil = linOpt.runLinearOptimizationModel(
            args.model_type, links, flows, traffic, timestamp, args.save_lp_models
        )
        logger.info("LINEAR OPTIMIZATION RETURNED!")
        return [timestamp, minLinkUtil, maxLinkUtil, avgLinkUtil]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "model_type",
        choices=[
            CalcType.BASELINE.value,
            CalcType.AVERAGE.value,
            CalcType.MAX.value,
            CalcType.SQUARED.value,
        ],
        help="type of calculation to run",
    )
    parser.add_argument(
        "-slpm",
        "--save-lp-models",
        action="store_true",
        help="save linear optimization models",
    )
    args = parser.parse_args()

    # Set start method to spawn to avoid issues with multiprocessing on Windows
    set_start_method("spawn")

    startTime = pd.Timestamp.now()
    logger.info("Started, model_type: " + str(args.model_type))

    flows = dataUtils.readFlows(DATA_DAY)
    links = dataUtils.readLinks()
    traffic = dataUtils.readTraffic(DATA_DAY)

    with mp.Pool(processes=dataUtils.CPU_THREADS) as pool:
        results = pool.starmap(
            process_flows_hour,
            [
                (timestamp, flows[timestamp], traffic[timestamp], args, links.copy())
                for timestamp in flows
            ],
        )

    logger.info("Finished processing all timestamps!")

    results.sort()
    dataUtils.writeDataToFile(
        pd.DataFrame(
            results, columns=["timestamp", "min_util", "max_util", "avg_util"]
        ),
        args.model_type,
    )

    endTime = pd.Timestamp.now()

    # Log elapsed time in hours, minutes and seconds
    elapsedTime = (endTime - startTime).components
    logger.info(
        f"Finished, elapsed time: {elapsedTime.hours} hours, {elapsedTime.minutes} minutes, {elapsedTime.seconds} seconds"
    )
