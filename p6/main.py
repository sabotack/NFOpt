import sys
import logging
import gurobipy as gp
from gurobipy import GRB

from p6.utils import network as nwUtils

logger = logging.getLogger(__name__)

# --- FUNCTIONS ---
def printSolution(m):
    if m.status == GRB.OPTIMAL:
        print('Optimal solution found')
        for v in m.getVars():
            print(f"{v.varName}: {v.x}")
    elif m.status == GRB.INFEASIBLE:
        print('Model is infeasible')


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
    

def main():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logging.basicConfig(filename='p6.log', level=logging.DEBUG)
    logger.addHandler(handler)
    
    logger.info('Started')
    logger.info('Finished')
    logger.debug('TESTESTTESTETSETEST')



    # --- LINKS ---
    linksCapacity = {}
    linksCapacity['AB'] = 600
    linksCapacity['AC'] = 2000
    linksCapacity['BD'] = 500
    linksCapacity['BE'] = 600
    linksCapacity['CF'] = 1500
    linksCapacity['DG'] = 400
    linksCapacity['EG'] = 600
    linksCapacity['FG'] = 1500

    # --- PATHS ---
    flows = {}
    flows['AG'] = {}
    flows['AG'][0] = ['A', 'B', 'D', 'G']
    flows['AG'][1] = ['A', 'B', 'E', 'G']
    flows['AG'][2] = ['A', 'C', 'F', 'G']

    # --- TRAFFIC ---
    traffic = {}
    traffic['AG'] = 100

    # --- RATIOS ---

    
    routersHash = nwUtils.getRoutersHashFromFlows(flows)
    
    links = {}
    nwUtils.recCalcRatios(links, routersHash['G'], linksCapacity)
    nwUtils.printRouterHash(routersHash)
    

    print("\n-------------------------------")

    currentRouter = routersHash['G']

    while(currentRouter.name != 'A'):
        print(currentRouter.name)
        currentRouter = currentRouter.ingress[list(currentRouter.ingress.keys())[len(currentRouter.ingress)-1]]
    
    print(currentRouter.name)


    for linkKey in links:
        print(f"Link: {linkKey} - Capacity: {links[linkKey].capacity} - Ratio: {links[linkKey].trafficRatio}")


if __name__ == '__main__':
    main()