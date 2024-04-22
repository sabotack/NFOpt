import gurobipy as gp

from gurobipy import GRB

from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
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
