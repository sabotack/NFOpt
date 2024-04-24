import gurobipy as gp
from gurobipy import GRB

# Links and their capacities
links, capacity = gp.multidict({
    ("A", "B"): 100,
    ("A", "C"): 200,
    ("B", "D"): 300,
    ("B", "E"): 400,
    ("C", "F"): 500,
    ("D", "G"): 600,
    ("E", "G"): 700,
    ("F", "G"): 800,
    ("L", "C"): 900,
    ("L", "H"): 1000,
    ("H", "G"): 1100
})

#Paths for each source-destination pair
Paths = {
    "AG": {
        0: ["A", "B", "D", "G"],
        1: ["A", "B", "E", "G"],
        2: ["A", "C", "F", "G"],
    },
    "LG": {
        0: ["L", "C", "F", "G"],
        1: ["L", "H", "G"]
    }
}

traffic = {
    "AG": 200,
    "LG": 200,
}


# Create optimization model
m = gp.Model("network_optimization")

# Decision variables for path ratios for each source-destination pair
path_ratios = m.addVars([(sd, pathNum) for sd in Paths for pathNum in Paths[sd]], vtype=GRB.CONTINUOUS, name="PathRatios")

# Auxiliary variable for the maximum link utilization
utilization = m.addVars(links, vtype=GRB.CONTINUOUS, name="Utilization")


m.setObjective(gp.quicksum((utilization[link]**2 for link in links)), GRB.MINIMIZE)

# Constraints for each link's utilization
for link in links:
    link_flow = gp.quicksum(
        path_ratios[sd, pathNum] * traffic[sd]
        if link in zip(Paths[sd][pathNum][:-1], Paths[sd][pathNum][1:])
        else 0
        for sd in Paths for pathNum in Paths[sd]
    )

    # Constraint that link flow must be less than or equal to the capacity (In prinicple can be removed-> Dataset contains links that have above 100% utilization)
    m.addConstr(link_flow <= capacity[link], name=f"cap_{link}")
    m.addConstr(link_flow == utilization[link] * capacity[link], name=f"util_{link}")

# Traffic split ratios must sum to 1 for each source-destination pair
for sd in traffic:
    m.addConstr(path_ratios.sum(sd, '*') == 1, name=f"traffic_split_{sd}")

# Write model to file (just debug) write
m.write("squaredUtilization.lp")

# Optimize the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    #find largest link util and print
    
    print(f"Optimal average link utilization: {m.getObjective().getValue() / len(links) * 100:.2f}%")
    for sd in Paths:
        print(f"Optimal path ratios for {sd}:")
        for pathNum in Paths[sd]:
            print(f"   Path {pathNum}: {path_ratios[sd, pathNum].x * 100:.2f} %")

    print("\n-----------------\n")
    # Calculate average link utilization
    totalLinkUtil = 0
    for link in links:
        link_flow = sum(
            path_ratios[sd, pathNum].x * traffic[sd]
            if link in zip(Paths[sd][pathNum][:-1], Paths[sd][pathNum][1:])
            else 0
            for sd in Paths for pathNum in Paths[sd]
        )
        print(f"Link {link} utilization: {link_flow / capacity[link] * 100:.2f}%")
        totalLinkUtil += link_flow / capacity[link] * 100
    totalLinkUtil = totalLinkUtil / len(links)
    print(f"Average link utilization: {totalLinkUtil:.2f}%")

else:
    print("No optimal solution found.")