from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
from p6.linearOptimization import LinearOptimization as linOpt
from p6.linearOptimization.LinearOptimization import LinearOptimizationModel as LinearOptimizationModel

logger = log.setupCustomLogger(__name__)

import pandas as pd

DATA_DAY = 2

# --- FUNCTIONS ---
def calcUtil(flows, traffic, linksCapacity, ratios):
    # Initialization
    totalLinkUtilization = 0
    linkUtilization = {}

    # Calculate linkUtil for all links in all flows
    for flow in flows:
        for path in flows[flow]:
            for link in flows[flow][path]:
                if link in linkUtilization:
                    linkUtilization[link] +=  traffic[flow] * ratios[flow][path] / linksCapacity[link] * 100
                else :
                    linkUtilization[link] = traffic[flow] * ratios[flow][path] / linksCapacity[link] * 100

    # avg link utilization calculation
    for link in linkUtilization:
        totalLinkUtilization += linkUtilization[link]

    avgLinkUtilization = totalLinkUtilization / len(linkUtilization)

    return (totalLinkUtilization, avgLinkUtilization, linkUtilization)

def calcUtilNew():
    return

def main():
    logger.info('Started')

    flows = dataUtils.readFlows(DATA_DAY)
    links = dataUtils.readLinks()
    traffic = dataUtils.readTraffic(DATA_DAY)

    for timestamp in flows:
        for linkKey in links:
            links[linkKey]['totalTraffic'] = 0

        for i, flow in enumerate(flows[timestamp]):
            routers = nwUtils.getRoutersHashFromFlow(flows[timestamp][flow])
            flowLinks = nwUtils.getFlowLinks(routers, links)

            for linkKey in flowLinks:
                # if links[linkKey]['totalTraffic'] not in links:
                #     links[linkKey]['totalTraffic'] = traffic[timestamp][flow]
                # else:
                #     links[linkKey]['totalTraffic'] += traffic[timestamp][flow]
                if(linkKey in links):
                    links[linkKey]['totalTraffic'] += traffic[timestamp][flow] * flowLinks[linkKey].trafficRatio
                else:
                    links[linkKey] = {
                        'linkStart': flowLinks[linkKey].linkStart,
                        'linkEnd': flowLinks[linkKey].linkEnd,
                        'capacity': flowLinks[linkKey].capacity,
                        'totalTraffic': traffic[timestamp][flow] * flowLinks[linkKey].trafficRatio
                        }

            # log every 1000 flows
            if(i % 10000 == 0):
                logger.info(f'Processed {timestamp} {i+1} flows of {len(flows[timestamp])}...')
            if(i == len(flows[timestamp]) - 1):
                logger.info(f'Processed {timestamp} {i+1} flows of {len(flows[timestamp])}...')
            
    
        for linkKey in links:
            procentage = links[linkKey]['totalTraffic'] / links[linkKey]['capacity'] * 100
            if(procentage >= 70):
                print(f'{timestamp} Link: {links[linkKey]}')
                print(f'{timestamp} - {procentage}%')

        #run linear optimization model
        linOpt.runLinearOptimizationModel(LinearOptimizationModel.averageUtilization, links, flows[timestamp], traffic[timestamp])
        #linOpt.runLinearOptimizationModel(LinearOptimizationModel.maxUtilization, links, flows[timestamp], traffic[timestamp])
        #linOpt.runLinearOptimizationModel(LinearOptimizationModel.squaredUtilization, links, flows[timestamp], traffic[timestamp])



 #make fake flows datahere
    # flows = {'Tue 00:00:00': {'AG': [['A', 'B', 'D', 'G'], ['A', 'B', 'E', 'G'], ['A', 'C', 'F', 'G']], 'LG': [['L', 'C', 'F', 'G'], ['L', 'H', 'G']]}}
    # links = {
    #     'AB': {'linkStart': 'A', 'linkEnd': 'B', 'capacity': 1000},
    #     'AC': {'linkStart': 'A', 'linkEnd': 'C', 'capacity': 1000},
    #     'BD': {'linkStart': 'B', 'linkEnd': 'D', 'capacity': 1000},
    #     'BE': {'linkStart': 'B', 'linkEnd': 'E', 'capacity': 1000},
    #     'CF': {'linkStart': 'C', 'linkEnd': 'F', 'capacity': 1000},
    #     'DG': {'linkStart': 'D', 'linkEnd': 'G', 'capacity': 1000},
    #     'EG': {'linkStart': 'E', 'linkEnd': 'G', 'capacity': 1000},
    #     'FG': {'linkStart': 'F', 'linkEnd': 'G', 'capacity': 1000},
    #     'LC': {'linkStart': 'L', 'linkEnd': 'C', 'capacity': 1000},
    #     'LH': {'linkStart': 'L', 'linkEnd': 'H', 'capacity': 1000},
    #     'HG': {'linkStart': 'H', 'linkEnd': 'G', 'capacity': 1000},
    # }
    # traffic = {'Tue 00:00:00': {'AG': 200, 'LG': 200}}
    
    #test data but thats real data
    # flows = {'Tue 00:00:00': {'R1004R1010': [['R1004', 'R1993', 'R1321', 'R1010'], ['R1004', 'R2264', 'R1321', 'R1010']]}}
    # links = {
    #         'R1004R1993': {'linkStart': 'R1004', 'linkEnd': 'R1993', 'capacity': 121212},
    #         'R1993R1321': {'linkStart': 'R1993', 'linkEnd': 'R1321', 'capacity': 303030},
    #         'R1004R2264': {'linkStart': 'R1004', 'linkEnd': 'R2264', 'capacity': 121212},
    #         'R2264R1321': {'linkStart': 'R2264', 'linkEnd': 'R2153', 'capacity': 272727},
    #         'R1321R1010': {'linkStart': 'R2153', 'linkEnd': 'R1010', 'capacity': 121212}
    #     }
    # traffic = {'Tue 00:00:00': {'R1004R1010': 3.506862}}
    