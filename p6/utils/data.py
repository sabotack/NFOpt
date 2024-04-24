import sys
import pandas as pd

from p6.utils import log
logger = log.setupCustomLogger(__name__)

DATASET_PATH = 'internal-dataset'

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
        logger.info('Started reading paths...')
        dataFlows = pd.read_csv(f'{DATASET_PATH}/flow-path-day{day}.csv', names=['timestamp', 'pathStart', 'pathEnd', 'path'], engine='pyarrow')
        dataFlows['pathName'] = dataFlows['pathStart'] + dataFlows['pathEnd']
        logger.info('Finished reading paths, number of paths: ' + str(len(dataFlows.index)))
        
        # Grouping paths by timestamp and pathName, and splitting the path string into a list of paths
        grouped_flows = dataFlows.groupby(['timestamp', 'pathName'])['path'].apply(lambda x: [path[1:-1].split(';') for path in x]).to_dict()
        
        # Constructing the final flows dictionary, only keeping flows with more than one path
        flows = {}
        for (timestamp, pathName), paths in grouped_flows.items():
            for path in paths:
                if len(path) > 1:
                    if timestamp not in flows:
                        flows[timestamp] = {}
                    flows[timestamp][pathName] = paths
            
        logger.info('Finished grouping paths, number of flows: ' + str(len(flows)))
    except Exception as e:
        logger.error(f'Error reading flows: {e}')
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
        logger.info('Started reading links...')
        dataCapacity = pd.read_csv(f'{DATASET_PATH}/links.csv.gz', compression="gzip", names=['linkStart', 'linkEnd', 'capacity'], skiprows=1, engine="pyarrow")
        dataCapacity['linkName'] = dataCapacity['linkStart'] + dataCapacity['linkEnd']
        dataCapacity.set_index('linkName', inplace=True)
        links = dataCapacity.to_dict('index')
        logger.info('Finished reading links, number of links: ' + str(len(links)))
    except Exception as e:
        logger.error(f'Error reading links: {e}')
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
        logger.info('Started reading traffic...')
        dataTraffic = pd.read_csv(f'{DATASET_PATH}/flow-traffic-day{day}.csv', names=['timestamp', 'flowStart', 'flowEnd', 'traffic'], engine='pyarrow')
        dataTraffic['flow'] = dataTraffic['flowStart'] + dataTraffic['flowEnd']
        dataTraffic = dataTraffic.drop(['flowStart','flowEnd'], axis=1)
        logger.info('Finished reading traffic, number of flows: ' + str(len(dataTraffic.index)))
        
        # Grouping traffic by timestamp and flow
        grouped_traffic = dataTraffic.groupby(['timestamp', 'flow'])['traffic'].first().to_dict()

        # Constructing the final traffic dictionary
        traffic = {}
        for (timestamp, flow), traffic_value in grouped_traffic.items():
            if timestamp not in traffic:
                traffic[timestamp] = {}
            traffic[timestamp][flow] = traffic_value

        logger.info('Finished grouping traffic, number of flows: ' + str(len(traffic)))
    except Exception as e:
        logger.error(f'Error reading traffic: {e}')
        sys.exit(1)

    return traffic
