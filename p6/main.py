import gurobipy as gp

from p6.utils import data as dataUtils
from p6.utils import network as nwUtils
from p6.utils import log
from p6.linearOptimization import LinearOptimization as linOpt
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

    # flows = dataUtils.readFlows(DATA_DAY)
    # links = dataUtils.readLinks()
    # traffic = dataUtils.readTraffic(DATA_DAY)
    
    
    #make fake flows datahere
    flows = {'Tue 00:00:00': {'AG': [['A', 'B', 'D', 'G'], ['A', 'B', 'E', 'G'], ['A', 'C', 'F', 'G']], 'LG': [['L', 'C', 'F', 'G'], ['L', 'H', 'G']]}}
    links = {
        'AB': {'linkStart': 'A', 'linkEnd': 'B', 'capacity': 1000},
        'AC': {'linkStart': 'A', 'linkEnd': 'C', 'capacity': 1000},
        'BD': {'linkStart': 'B', 'linkEnd': 'D', 'capacity': 1000},
        'BE': {'linkStart': 'B', 'linkEnd': 'E', 'capacity': 1000},
        'CF': {'linkStart': 'C', 'linkEnd': 'F', 'capacity': 1000},
        'DG': {'linkStart': 'D', 'linkEnd': 'G', 'capacity': 1000},
        'EG': {'linkStart': 'E', 'linkEnd': 'G', 'capacity': 1000},
        'FG': {'linkStart': 'F', 'linkEnd': 'G', 'capacity': 1000},
        'LC': {'linkStart': 'L', 'linkEnd': 'C', 'capacity': 1000},
        'LH': {'linkStart': 'L', 'linkEnd': 'H', 'capacity': 1000},
        'HG': {'linkStart': 'H', 'linkEnd': 'G', 'capacity': 1000},
    }
    traffic = {'Tue 00:00:00': {'AG': 200, 'LG': 200}}
    
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

        # run through traffic and remove the ones that reference itself:
        for trafficKey in list(traffic[timestamp]):
            first_router, second_router = trafficKey[:5], trafficKey[5:]
            # Check if the router IDs are the same
            if first_router == second_router:
                traffic[timestamp].pop(trafficKey)

        # run through traffic and remove the ones that reference itself:
        print("Duplicate Traffic removed:")
        for trafficKey in traffic[timestamp]:
            # Split the traffic key into two router IDs
            first_router, second_router = trafficKey[:5], trafficKey[5:]
            # Check if the router IDs are the same
            if first_router == second_router:
               print(f"{trafficKey} is a duplicate.")
        
        # remove duplicate flows
        for flowKey in list(flows[timestamp]):
            first_router, second_router = flowKey[:5], flowKey[5:]
            if first_router == second_router:
                flows[timestamp].pop(flowKey)

        print("Duplicate Flows removed:")
        for flowKey in flows[timestamp]:
            first_router, second_router = flowKey[:5], flowKey[5:]
            if first_router == second_router:
                print(f"{flowKey} is a duplicate.")

        # remove duplicate links
        for linkKey in list(links):
            first_router, second_router = linkKey[:5], linkKey[5:]
            if first_router == second_router:
                links.pop(linkKey)
        
        print("Duplicate Links removed:")
        for linkKey in links:
            first_router, second_router = linkKey[:5], linkKey[5:]
            if first_router == second_router:
                print(f"{linkKey} is a duplicate.")

        #run linear optimization model
        linOpt.runLinearOptimizationModel('averageUtilization', links, flows[timestamp], traffic[timestamp])
        #linOpt.runLinearOptimizationModel('maxUtilization', links, flows[timestamp], traffic[timestamp])
        #linOpt.runLinearOptimizationModel('squaredUtilization', links, flows[timestamp], traffic[timestamp])
        break


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
