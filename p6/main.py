import argparse
import gurobipy as gp
from gurobipy import GRB

import statistics as stats

from p6.calc_type_enum import CalcType
from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
from p6.linearOptimization import LinearOptimization as linOpt

logger = log.setupCustomLogger(__name__)

import pandas as pd

DATA_DAY = 2

def calcLinkUtil(links):
    util = {}

    for linkKey in links:
        util[linkKey] = links[linkKey]['totalTraffic'] / links[linkKey]['capacity'] * 100

    return util

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_type', choices=[CalcType.BASELINE.value, CalcType.AVERAGE.value, CalcType.MAX.value, CalcType.SQUARED.value], help='type of calculation to run')
    args = parser.parse_args()

    logger.info('Started, model_type: ' + str(args.model_type))

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
        if (args.model_type == CalcType.BASELINE.value):
            linkUtil = calcLinkUtil(links)
            dailyUtil.append([timestamp, min(linkUtil.values()), max(linkUtil.values()), stats.mean(linkUtil.values())]) 
        else:
            avgLinkUtil, minLinkUtil, maxLinkUtil = linOpt.runLinearOptimizationModel(args.model_type, links, flows[timestamp], traffic[timestamp], timestamp)
            optUtil.append([timestamp, minLinkUtil, maxLinkUtil, avgLinkUtil])

    if (args.model_type == CalcType.BASELINE.value):
        dataUtils.writeDataToFile(pd.DataFrame(dailyUtil, columns=['timestamp', 'min_util', 'max_util', 'avg_util']), args.model_type)
    else:
        dataUtils.writeDataToFile(pd.DataFrame(optUtil, columns=['timestamp', 'min_util', 'max_util', 'avg_util']), args.model_type)
