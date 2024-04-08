import gurobipy as gp
from gurobipy import GRB

# --- FUNCTIONS ---
def printSolution(m):

    if m.status == GRB.OPTIMAL:
        print('Optimal solution found')
        for v in m.getVars():
            print(f"{v.varName}: {v.x}")
    elif m.status == GRB.INFEASIBLE:
        print('Model is infeasible')


def calcAvgLinkUtil(flows, traffic, linksCapacity, ratios):
    totalLinkUtilization = 0
    linkUtilization = {}

    # --- TRAFFIC OVER LINKS ---
    trafficOverLinks = {}

    # traffic calculation over links
    for flow in flows:
        for path in flows[flow]:
            for link in flows[flow][path]:
                if link in trafficOverLinks:
                    trafficOverLinks[link] +=  traffic[flow] * ratios[flow][path]
                else :
                    trafficOverLinks[link] = traffic[flow] * ratios[flow][path]


    # link utilization calculation
    for link in trafficOverLinks:
        if link in linkUtilization :
            linkUtilization[link] += trafficOverLinks[link] / linksCapacity[link] * 100
        else :
            linkUtilization[link] = trafficOverLinks[link] / linksCapacity[link] * 100
        #print(f"Link: {link} has {linkUtilization[link]}% link util")

    # avg link utilization calculation
    for link in linkUtilization:
        totalLinkUtilization += linkUtilization[link]

    avgLinkUtilization = totalLinkUtilization / len(linkUtilization)

    return (totalLinkUtilization, avgLinkUtilization, linkUtilization)

def main():
    # --- LINKS ---
    linksCapacity = {}
    linksCapacity['AB'] = 600
    linksCapacity['AC'] = 2000
    linksCapacity['BD'] = 500
    linksCapacity['BE'] = 600
    linksCapacity['CF'] = 1500
    linksCapacity['DG'] = 400
    linksCapacity['EG'] = 400
    linksCapacity['FG'] = 1500

    # --- PATHS ---
    flows = {}
    flows['AG'] = {}
    flows['AG'][0] = ['AB', 'BE', 'EG']
    flows['AG'][1] = ['AB', 'BD', 'DG']
    flows['AG'][2] = ['AC', 'CF', 'FG']

    # --- TRAFFIC ---
    traffic = {}
    traffic['AG'] = 100

    # --- RATIOS ---

    ratios = {}
    ratios['AG'] = {}

    for path in flows['AG']:
        ratios['AG'][path] = 1/len(flows['AG'])


    (totalLinkUtilization, avgLinkUtilization, linkUtilization) = calcAvgLinkUtil(flows, traffic, linksCapacity, ratios)

    m = gp.Model('utilization_optimization')

    for flow in flows:
        for r in ratios[flow]:
            ratios[flow][r] = m.addVar(vtype=GRB.CONTINUOUS, name=f"ratio_{r}")
            print(f"Ratio: {ratios[flow][r]}")


    # Objective function
    m.ModelSense = GRB.MINIMIZE
    m.setObjective(totalLinkUtilization, GRB.MINIMIZE)

    # Constraints
    for link in linkUtilization:
        m.addConstr(linkUtilization[link] <= 100, name=f"linkUtil_{link}")

    for flow in flows:
        m.addConstr(sum(ratios[flow].values()) == 1, name="sumRatios")

    m.write("test.lp")

    m.optimize()

    printSolution(m)

    print(f"Initial Avg link utilization: {avgLinkUtilization}%")

    # --- calculate new Ratios ---
    newRatios = {}
    newRatios['AG'] = {}
    for r in ratios['AG']:
        newRatios['AG'][r] = float(ratios['AG'][r].x)

    #print(f"New Ratios: {newRatios}")

    #print(f"New Avg link utilization: {calcAvgLinkUtil(newRatios)}%")
