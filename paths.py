import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np

TRAFFIC_HOUR_0 = 699638
PATHS_HOUR_0 = 2349348
traffic_per_path = {}
graph_hash = {}
ratio_hash = {}
capacity_per_path = {}
path_names = ['timeStamp', 'pathStart', 'pathEnd', 'linksInPath']
traffic_names = ['timeStamp', 'pathStart', 'pathEnd', 'traffic']
total_time_convert = 0
total_time_paths = 0
total_time_traffic = 0
total_time_read = []

LR = 0.3
ITERATIONS = 1
OFFSET = -0.8

# Functions -------------------------------------------------------------------
def numRouters_to_pathArr(num_routers, path_str):
    path = []
    router = ""
    path_str = path_str[1:-1]
    for i in range(num_routers):
        router = path_str[i*6:i*6+5]
        path.append(router)
    return path

def pathStr_to_pathArr(path_str):
    start = time.time()
    
    router_count = path_str.count('R')
    path = numRouters_to_pathArr(router_count, path_str)
    end = time.time()
    global total_time_convert
    total_time_convert += end - start
    return path

def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# Read the link capacities and store them in a hash table ---------------------
start_r = time.time()
links = pd.read_csv('dataset-week/links.csv.gz', compression='gzip')
links_hash = {}
for i in links.index:
    links_hash[links['linkStart'][i] + links['linkEnd'][i]] = links['capacity'][i]
print('Done reading links')
end_r = time.time()
total_time_read.append(int(end_r - start_r))

# Read the traffic for all flows ----------------------------------------------
start_r = time.time()
traffic = pd.read_csv('dataset-week/flow-traffic-day1.csv.gz', compression='gzip', names=traffic_names, low_memory=False, nrows=TRAFFIC_HOUR_0)
traffic['pathName'] = traffic['pathStart'] + traffic['pathEnd']
traffic = traffic.drop(['pathStart','pathEnd','timeStamp'], axis=1)
traffic_index = ['pathName', 'traffic']
traffic = traffic.reindex(columns=traffic_index)
traffic = dict(traffic.values)
print('Done reading traffic')
end_r = time.time()
total_time_read.append(int(end_r - start_r))

# Iterate over the entries ----------------------------------------------------
start_r = time.time()
cur_paths = []
paths = pd.read_csv('dataset-week/flow-paths-day1.csv.gz', compression='gzip', names=path_names, low_memory=False, nrows=PATHS_HOUR_0)
paths['pathName'] = paths['pathStart'] + paths['pathEnd']
paths = paths.drop(['pathStart','pathEnd'], axis=1)
print('Done reading paths')
end_r = time.time()
total_time_read.append(int(end_r - start_r))

cur_flow_name = paths['pathName'][0] # Initialize the current flow name
start_p = time.time()
for i in paths.index:
    name = paths['pathName'][i]
    if name == cur_flow_name:
        path = pathStr_to_pathArr(paths['linksInPath'][i])
        cur_paths.append(path)
    else:
        # Perform calculations for the current flow ---------------------------
        # Check if the current flow is in the traffic hash table --------------
        if cur_flow_name in traffic.keys():
            start_t = time.time()
            ratio_per_path = 1/len(cur_paths)
            graph_hash[cur_flow_name] = cur_paths
            flow_weights = []
            flow_traffic = []
            path_capacity = []

            for path in cur_paths:
                capacity = 0
                # Add the weights for each path
                flow_weights.append(ratio_per_path)
                # Calculate the amount of traffic that passes through each path
                # times len(path)-1 is equal to the number of links
                flow_traffic.append(traffic[cur_flow_name] * ratio_per_path)
                for i in range(len(path) - 1):
                    link = path[i] + path[i + 1]
                    if link in links_hash:
                        capacity += links_hash[link]
                path_capacity.append(capacity)

            ratio_hash[cur_flow_name] = flow_weights
            traffic_per_path[cur_flow_name] = flow_traffic
            capacity_per_path[cur_flow_name] = path_capacity
            end_t = time.time()
            total_time_traffic += end_t - start_t

        # Reset the current flow and add the next path to the array --------
        cur_flow_name = name
        cur_paths = []
        path = pathStr_to_pathArr(paths['linksInPath'][i])
        cur_paths.append(path)
end_p = time.time()
total_time_paths = end_p - start_p
print('Done calculating traffic per link')


# Calculate path utilization -----------------------------------------
def calc_path_util(traffic_per_path, capacity_per_path):
    for flow in traffic_per_path:
        print(f"\nFlow: {flow}")
        for path_traffic in traffic_per_path[flow]:
            print(f"Traffic: {path_traffic}")
        for path_capacity in capacity_per_path[flow]:
            print(f"Capacity: {path_capacity}")


# Print the times -------------------------------------------------------------
print(f'Time spent reading: {total_time_read[0]} seconds')
print(f'Time spent reading: {total_time_read[1]} seconds')
print(f'Time spent reading: {total_time_read[2]} seconds')
print(f'Total time spent converting string: {int(total_time_convert)} seconds')
print(f'Total time spent calculating paths: {int(total_time_paths)} seconds')
print(f'Total time spent calculating traffic: {int(total_time_traffic)} seconds')

# Run path util ---
calc_path_util(traffic_per_path, capacity_per_path)

# Sort the traffic per link hash table on procent util ------------------------
# traffic_per_link = dict(sorted(traffic_per_link.items(), key=lambda item: item[1], reverse=True))

# Make a graph of the traffic per link ----------------------------------------
# x = list(traffic_per_link.keys())
# y = list(traffic_per_link.values())
# plt.plot(x, y)
# plt.xlabel('Links')
# plt.ylabel('Utilization (%)')
# plt.xticks(rotation=60)
# plt.xticks(range(0, len(x), 300))
# plt.show()

# Backpropagation on the graphs to update weights -----------------------------
print(f"\nInitial ratios:\n{list(ratio_hash.items())[:30]}")
for i in range(ITERATIONS):
    for flow in graph_hash:
        path_weight = 0
        flow_weights = []
        for path in graph_hash[flow]:
            # Update the weight of the link
            flow_weights.append(
                sigmoid(
                    ratio_hash[flow][path_weight]
                    + (sigmoid(traffic_per_path) + OFFSET) * LR
                )
            )
            path_weight += 1

        ratio_hash[flow] = flow_weights
print(f"\nNew ratios:\n{list(ratio_hash.items())[:30]}")
