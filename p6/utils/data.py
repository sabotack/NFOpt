import os
import sys
import pandas as pd
import multiprocessing as mp

from p6.utils import log
from functools import partial
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("variables.env")
logger = log.setupCustomLogger(__name__)

DATASET_PATH = os.getenv("DATASET_PATH")
DATASET_PATHS_PREFIX = os.getenv("DATASET_PATHS_PREFIX")
DATASET_TRAFFIC_PREFIX = os.getenv("DATASET_TRAFFIC_PREFIX")
DATASET_LINKS_NAME = os.getenv("DATASET_LINKS_NAME")

DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR")
RATIOS_OUTPUT_DIR = os.getenv("RATIOS_OUTPUT_DIR")


def _process_group(chunk, group_func):
    return chunk.groupby(["timestamp", "pathName"])["path"].apply(group_func)


def _group_func(x):
    return [path[1:-1].split(";") for path in x]


def _merge_results(results):
    return {k: v for result in results for k, v in result.items()}


def readFlows(day):
    """
    Reads the flow paths from the dataset and returns a dictionary with the flows grouped by timestamp and pathName.
    The paths are also split into a list of paths.

    ### Parameters:
    ----------
    #### day: int
    The day of the dataset to read the flows from.

    ### Returns:
    ----------
    A dictionary with the flows grouped by timestamp and pathName, with the paths split into a list of paths.
    """

    try:
        logger.info("START: reading flows...")

        logger.info("Reading paths...")
        dataFlows = pd.read_csv(
            f"{DATASET_PATH}/{DATASET_PATHS_PREFIX}{day}.csv",
            names=["timestamp", "pathStart", "pathEnd", "path"],
            engine="pyarrow",
        )
        dataFlows["pathName"] = dataFlows["pathStart"] + dataFlows["pathEnd"]
        logger.info(
            "Finished reading paths, number of paths: " + str(len(dataFlows.index))
        )

        # Grouping paths by timestamp and pathName, and splitting the path string into a list of paths
        logger.debug("Grouping paths...")

        # Splitting data into chunks for multiprocessing
        cpu_count = mp.cpu_count()
        chunk_size = len(dataFlows) // cpu_count
        logger.info(
            f"Grouping in parallel | CPUs: {cpu_count} | chunk_size: {chunk_size} | len(dataFlows): {len(dataFlows)}"
        )
        chunks = [
            (
                dataFlows[i:]
                if rangeIndex == cpu_count - 1
                else dataFlows[i : i + chunk_size]
            )
            for rangeIndex, i in enumerate([i * chunk_size for i in range(cpu_count)])
        ]

        partial_process_group = partial(_process_group, group_func=_group_func)

        # Create a pool of processes and apply the process_group function to each chunk
        with mp.Pool() as pool:
            results = pool.map(partial_process_group, chunks)

        # Merge the results from all processes
        grouped_flows = _merge_results(results)

        # grouped_flows = dataFlows.groupby(['timestamp', 'pathName'])['path'].apply(lambda x: [path[1:-1].split(';') for path in x]).to_dict()
        logger.debug("Finished grouping paths")

        # Constructing the final flows dictionary, only keeping paths with more than one router in path
        logger.debug("Constructing flows dictionary...")
        flows = {}
        for (timestamp, pathName), paths in grouped_flows.items():
            for path in paths:
                # Only keep paths with more than one router (link has to have at least 2 routers)
                # Also dont add paths that start and end at the same router
                if len(path) > 1 and pathName[:5] != pathName[5:]:
                    if timestamp not in flows:
                        flows[timestamp] = {}
                    flows[timestamp][pathName] = paths
        logger.debug("Finished constructing flows dictionary")

        logger.info("END: reading flows, number of groups: " + str(len(flows)))
    except Exception as e:
        logger.error(f"Error reading flows: {e}")
        sys.exit(1)

    return flows


def readLinks():
    """
    Reads the links capacities from the dataset and returns a dictionary with the links indexed by linkName.

    ### Returns:
    ----------
    A dictionary with the links indexed by linkName.
    """

    try:
        logger.info("START: reading links...")

        logger.info("Reading links...")
        dataCapacity = pd.read_csv(
            f"{DATASET_PATH}/{DATASET_LINKS_NAME}.csv.gz",
            compression="gzip",
            names=["linkStart", "linkEnd", "capacity"],
            skiprows=1,
            engine="pyarrow",
        )
        dataCapacity["linkName"] = dataCapacity["linkStart"] + dataCapacity["linkEnd"]
        dataCapacity.set_index("linkName", inplace=True)
        links = dataCapacity.to_dict("index")
        # remove links that start and end at the same router - update: this is not necessary cant find any duplicates
        # copilot cooked here 🤨
        # links = {k: v for k, v in links.items() if k[:5] != k[5:]}
        logger.info("Finished reading links, number of links: " + str(len(links)))

        logger.info("END: reading links")
    except Exception as e:
        logger.error(f"Error reading links: {e}")
        sys.exit(1)

    return links


def readTraffic(day):
    """
    Reads the traffic from the dataset and returns a dictionary with the traffic grouped by timestamp and flow.

    ### Parameters:
    ----------
    #### day: int
    The day of the dataset to read the traffic from.

    ### Returns:
    ----------
    A dictionary with the traffic grouped by timestamp and flow.
    """

    try:
        logger.info("START: reading traffic...")

        logger.info("Started reading traffic...")
        dataTraffic = pd.read_csv(
            f"{DATASET_PATH}/{DATASET_TRAFFIC_PREFIX}{day}.csv",
            names=["timestamp", "flowStart", "flowEnd", "traffic"],
            engine="pyarrow",
        )
        dataTraffic["flow"] = dataTraffic["flowStart"] + dataTraffic["flowEnd"]
        dataTraffic = dataTraffic.drop(["flowStart", "flowEnd"], axis=1)
        logger.info(
            "Finished reading traffic, number of flows: " + str(len(dataTraffic.index))
        )

        # Grouping traffic by timestamp and flow
        logger.debug("Grouping traffic...")
        grouped_traffic = (
            dataTraffic.groupby(["timestamp", "flow"])["traffic"].first().to_dict()
        )
        logger.debug("Finished grouping traffic")

        # Constructing the final traffic dictionary
        logger.debug("Constructing traffic dictionary...")
        traffic = {}
        for (timestamp, flow), traffic_value in grouped_traffic.items():
            if timestamp not in traffic:
                traffic[timestamp] = {}
            # dont add traffic that starts and ends at the same router
            if flow[:5] == flow[5:]:
                continue
            traffic[timestamp][flow] = traffic_value
        logger.debug("Finished constructing traffic dictionary")

        logger.info("END: reading traffic, number of groups: " + str(len(traffic)))
    except Exception as e:
        logger.error(f"Error reading traffic: {e}")
        sys.exit(1)

    return traffic


def readRatios(date, type, day):
    """
    Reads the path ratios from the dataset and returns a dictionary with the ratios grouped by timestamp and pathName.

    ### Parameters:
    ----------
    #### date: str
    The date of the ratios to read in format YYYYMMDD.
    #### type: str
    The type of ratios to read.
    #### day: str
    The day of the week of the ratios to read.

    ### Returns:
    ----------
    A dictionary with the ratios grouped by timestamp and pathName.
    """

    try:
        logger.info("START: reading ratios...")
        ratios = {}
        for i in range(24):
            timestamp = ''
            iStr = "%02d" % i
            logger.info(f"Reading ratios for hour {iStr} ...")

            dataRatios = pd.read_csv(
                f"{RATIOS_OUTPUT_DIR}/{date}_{type}_{day}{iStr}_ratios.csv",
                names=["timestamp", "flowName", "pathNum", "ratio"],
                engine="pyarrow",
            )
            timestamp = dataRatios.iloc[1]["timestamp"]
            dataRatios.drop(["timestamp"], axis=1, inplace=True)
            dataRatios.set_index(["flowName", "pathNum"], inplace=True)

            ratios[timestamp] = dataRatios.to_dict()["ratio"]
            logger.info(
                f"Finished reading ratios for hour {iStr}, timestamp: {timestamp}, number of ratios: {str(len(dataRatios.index))}"
            )

        logger.info("END: reading ratios, number of groups: " + str(len(ratios)))
    except Exception as e:
        logger.error(f"Error reading ratios: {e}")
        sys.exit(1)

    return ratios


def writeDataToFile(data, type, ratioData=None):
    """
    Writes the daily utilization data to a CSV file.

    ### Parameters:
    ----------
    #### data: pandas.DataFrame
    The daily utilization data to write to a file.
    """

    try:
        if not os.path.exists(DATA_OUTPUT_DIR):
            os.makedirs(DATA_OUTPUT_DIR)

        filePath = ""
        timestamp = datetime.now().strftime("%Y%m%d")

        if ratioData is not None:
            if not os.path.exists(RATIOS_OUTPUT_DIR):
                os.makedirs(RATIOS_OUTPUT_DIR)

            time = (data["timestamp"][0][:3] + data["timestamp"][0][4:-6]).lower()
            filePath = f"{RATIOS_OUTPUT_DIR}/{timestamp}_{type}_{time}_ratios.csv"
        else:
            filePath = f"{DATA_OUTPUT_DIR}/{timestamp}_{type}.csv"

        logger.info(f"Writing data to file...")
        data.to_csv(filePath, mode="w", header=True, index=False)
        logger.info(f"Finished writing data to file")
    except Exception as e:
        logger.error(f"Error writing data to file: {e}")
        sys.exit(1)
