from pulp import *
import pandas as pd

# Parse data from csv files
routers = pd.read_csv('../dataset-week/routers.csv', names=['router'])

# read links from links.csv
links = pd.read_csv('../dataset-week/links.csv.gz', names=['linkStart', 'linkEnd', 'capacity'], compression='gzip')

# read traffic from flow-traffic-day1.csv
traffic_paths = pd.read_csv('../dataset-week/flow-traffic-day1.csv.gz', names=['timestamp', 'pathStart', 'pathEnd', 'traffic'], compression='gzip')

# read paths from flow-paths-day1.csv
paths = pd.read_csv('../dataset-week/flow-paths-day1.csv.gz', names=['timestamp', 'pathStart', 'pathEnd', 'path'], compression='gzip')

# # Define the problem
# prob = LpProblem("TrafficOptimization", LpMinimize)

# # Decision variables
# # Assuming you have already parsed the data and have information about routers, links, traffic
# # Create decision variables for flow on each path
# paths = [(start, end) for start, end in traffic_paths]
# flow = LpVariable.dicts("Flow", paths, lowBound=0, cat="Continuous")

# # Objective function
# prob += lpSum(flow[start, end] for start, end in paths)

# # Constraints
# # Capacity constraints
# for start, end, capacity in links:
#     prob += flow[start, end] <= capacity

# # Flow conservation constraints
# for router in routers:
#     if router != traffic_start and router != traffic_end:
#         # Sum of flows entering = sum of flows leaving
#         prob += lpSum(flow[start, router] for start, _ in paths if _ == router) == \
#                 lpSum(flow[router, end] for _, end in paths if _ == router)

# # Solve the problem
# prob.solve()

# # Print the results
# for v in prob.variables():
#     print(v.name, "=", v.varValue)
# print("Total Traffic =", value(prob.objective))
