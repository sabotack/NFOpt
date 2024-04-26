import gurobipy as gp
from gurobipy import GRB

import statistics as stats

from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
from p6.linearOptimization import LinearOptimization as linOpt
from p6.linearOptimization.LinearOptimization import LinearOptimizationModel

logger = log.setupCustomLogger(__name__)

import pandas as pd

DATA_DAY = 2

def calcLinkUtil(links):
    util = {}

    for linkKey in links:
        util[linkKey] = links[linkKey]['totalTraffic'] / links[linkKey]['capacity'] * 100

    return util

def _optimizeAverageUtilization():
    main(LinearOptimizationModel.averageUtilization)

def _optimizeMaxUtilization():
    main(LinearOptimizationModel.maxUtilization)

def _optimizeSquaredUtilization():
    main(LinearOptimizationModel.squaredUtilization)

def _baseline():
    main(None)

def main(optimizeType):
    logger.info('Started, optimizeType: ' + str(optimizeType))

    flows = dataUtils.readFlows(DATA_DAY)
    links = dataUtils.readLinks()
    traffic = dataUtils.readTraffic(DATA_DAY)

    dailyUtil = []
    optUtil = []

    for timestamp in flows:
        # Reset totalTraffic for all links in this timestamp
        for linkKey in links:
            links[linkKey]['totalTraffic'] = 0
            links[linkKey]['listFlows'] = []

        logger.info(f'Processing {timestamp} with {len(flows[timestamp])} flows...')
        for flow in flows[timestamp]:
            routers = nwUtils.getRoutersHashFromFlow(flows[timestamp][flow])
            flowLinks = nwUtils.getFlowLinks(routers, links)

            # Update links with traffic
            for linkKey in flowLinks:
                if(linkKey in links):
                    links[linkKey]['totalTraffic'] += traffic[timestamp][flow] * flowLinks[linkKey].trafficRatio
                else:
                    links[linkKey] = {
                        'linkStart': flowLinks[linkKey].linkStart,
                        'linkEnd': flowLinks[linkKey].linkEnd,
                        'capacity': flowLinks[linkKey].capacity,
                        'totalTraffic': traffic[timestamp][flow] * flowLinks[linkKey].trafficRatio
                        }
                    links[linkKey]['listFlows'] = []
                
                links[linkKey]['listFlows'].append(flow)

        #run linear optimization or baseline calculations
        if (optimizeType != None):
            avgLinkUtil, minLinkUtil, maxLinkUtil = linOpt.runLinearOptimizationModel(optimizeType, links, flows[timestamp], traffic[timestamp], timestamp)
            optUtil.append([timestamp, minLinkUtil, maxLinkUtil, avgLinkUtil])
        else:
            linkUtil = calcLinkUtil(links)
            dailyUtil.append([timestamp, min(linkUtil.values()), max(linkUtil.values()), stats.mean(linkUtil.values())]) 


    if (optimizeType != None):
        dataUtils.writeDataToFile(pd.DataFrame(optUtil, columns=['timestamp', 'min_util', 'max_util', 'avg_util']), optimizeType)
    else:
        dataUtils.writeDataToFile(pd.DataFrame(dailyUtil, columns=['timestamp', 'min_util', 'max_util', 'avg_util']), dataUtils.DataType.BASELINE)
    
    # logger.debug(f"Flows: {len(flows)}")

    # for flow in flows:
    #     print(f"Flow: {flow}")
    #     for path in flows[flow]:
    #         print(f"-: {path}")
    #     print("\n")

    # # --- LINKS ---
    # linksCapacity = {}
    # linksCapacity['AB'] = 600
    # linksCapacity['AC'] = 2000
    # linksCapacity['BD'] = 500
    # linksCapacity['BE'] = 600
    # linksCapacity['CF'] = 1500
    # linksCapacity['DG'] = 400
    # linksCapacity['EG'] = 600
    # linksCapacity['FG'] = 1500

    # # --- PATHS ---
    # flows = {}
    # flows['AG'] = {}
    # flows['AG'][0] = ['A', 'B', 'D', 'G']
    # flows['AG'][1] = ['A', 'B', 'E', 'G']
    # flows['AG'][2] = ['A', 'C', 'F', 'G']

    # # --- TRAFFIC ---
    # traffic = {}
    # traffic['AG'] = 100

    # # --- RATIOS ---

    # logger.info('Populating routers hash from flows')
    # routersHash = nwUtils.getRoutersHashFromFlows(flows)
    
    # logger.info('Calculating ratios')
    # links = {}
    # nwUtils.recCalcRatios(links, routersHash['G'], linksCapacity)
