import gurobipy as gp
from gurobipy import GRB
# --- FUNCTIONS ---
def printSolution():

    if m.status == GRB.OPTIMAL:
        print('Optimal solution found')
        for v in m.getVars():
            print(f"{v.varName}: {v.x}")
    elif m.status == GRB.INFEASIBLE:
        print('Model is infeasible')
    

def main(ratios):

    # --- TRAFFIC OVER LINKS ---
    trafficOverLinks = {}
    trafficOverLinks['AB'] = 0
    trafficOverLinks['AC'] = 0
    trafficOverLinks['BD'] = 0
    trafficOverLinks['BE'] = 0
    trafficOverLinks['CF'] = 0
    trafficOverLinks['DG'] = 0
    trafficOverLinks['EG'] = 0
    trafficOverLinks['FG'] = 0

    # --- AVG Link Utilization for each link ---
    linkUtilization['AB'] = 0
    linkUtilization['AC'] = 0
    linkUtilization['BD'] = 0
    linkUtilization['BE'] = 0
    linkUtilization['CF'] = 0
    linkUtilization['DG'] = 0
    linkUtilization['EG'] = 0
    linkUtilization['FG'] = 0


    avgLinkUtilization = 0
    # traffic calculation over links
    for path in flows['AG']:
        for link in flows['AG'][path]:
            #print('Link: ' + link)
            #print(f"Ratio: {ratios['AG']}")
            trafficOverLinks[link] +=  traffic['AG'] * ratios['AG'][path]

    # link utilization calculation
    for link in trafficOverLinks:
        linkUtilization[link] = trafficOverLinks[link] / linksCapacity[link] * 100
        #print(f"Link: {link} has {linkUtilization[link]}% link util")

    # avg link utilization calculation
    for link in linkUtilization:
        avgLinkUtilization += linkUtilization[link]

    avgLinkUtilization = avgLinkUtilization / len(linkUtilization)

    return avgLinkUtilization

# --- temp ---
linkUtilization = {}
linkUtilization['AB'] = 0
linkUtilization['AC'] = 0
linkUtilization['BD'] = 0
linkUtilization['BE'] = 0
linkUtilization['CF'] = 0
linkUtilization['DG'] = 0
linkUtilization['EG'] = 0
linkUtilization['FG'] = 0

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


avgLinkUtilization = main(ratios)

m = gp.Model('utilization_optimization')

for r in ratios['AG']:
    ratios['AG'][r] = m.addVar(vtype=GRB.CONTINUOUS, name=f"ratio_{r}")
    print(f"Ratio: {ratios['AG'][r]}")


# Objective function
m.ModelSense = GRB.MINIMIZE
m.setObjective(sum(linkUtilization.values()), GRB.MINIMIZE)

# Constraints
for link in linkUtilization:
    m.addConstr(linkUtilization[link] <= 100, name=f"linkUtil_{link}")

m.addConstr(sum(ratios['AG'].values()) == 1, name="sumRatios")

m.write("test.lp")

m.optimize()

printSolution()


print(f"Initial Avg link utilization: {avgLinkUtilization}%")

# --- calculate new Ratios ---
newRatios = {}
newRatios['AG'] = {}
for r in ratios['AG']:
    newRatios['AG'][r] = float(ratios['AG'][r].x)

#print(f"New Ratios: {newRatios}")

#print(f"New Avg link utilization: {main(newRatios)}%")


