import os
import gurobipy as gp
import pandas as pd
from collections import deque

from dotenv import load_dotenv
from p6.utils import log
from p6.utils import data as dataUtils


logger = log.setupCustomLogger(__name__)
load_dotenv("variables.env")

options = {
    "WLSACCESSID": os.getenv("WLSACCESSID"),
    "WLSSECRET": os.getenv("WLSSECRET"),
    "LICENSEID": int(os.getenv("LICENSEID")),
}

def find_reachable_nodes(graph, source, max_depth):
    visited = set()
    queue = deque([(source, 0)])  # Queue now stores tuples of (node, depth)
    reachable_nodes = set()
    reachable_edges = []

    while queue:
        node, depth = queue.popleft()
        if node not in visited and depth <= max_depth:
            visited.add(node)
            reachable_nodes.add(node)
            if depth < max_depth:  # Only add neighbors if within max_depth
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))  # Increment depth
                        reachable_edges.append((node, neighbor))  # Add the edge to the list
    return reachable_nodes, reachable_edges

def build_graph(edges):
    graph = {}
    for start, end in edges:
        if start not in graph:
            graph[start] = []
        if end not in graph:
            graph[end] = []
        graph[start].append(end)
        graph[end].append(start)
    return graph


def optMC(parserArgs, links, flowTraffic, timestamp):
    with gp.Env(params=options) as env, gp.Model(env=env) as m:
        m = gp.Model("netflow", env=env)
        # example of link data
        # links = {
        #     "A;B": {"capacity": 100},
        #     "A;C": {"capacity": 80},
        #     "B;D": {"capacity": 140},
        #     "B;E": {"capacity": 120},
        #     "C;F": {"capacity": 70},
        #     "D;G": {"capacity": 120},
        #     "E;G": {"capacity": 120},
        #     "F;G": {"capacity": 120},
        #     "X;C": {"capacity": 100},
        #     "X;Y": {"capacity": 100},
        #     "Y;F": {"capacity": 100},
        #     "R1;R2": {"capacity": 100},
        #     "R1;R3": {"capacity": 80},
        #     "R2;R4": {"capacity": 140},
        #     "R2;R5": {"capacity": 120},
        #     "R3;R6": {"capacity": 70},
        # } 

        # links = {
        #     "R1000;R1002": {"capacity": 100},
        #     "R1000;R1003": {"capacity": 80},
        #     "R1002;R2000": {"capacity": 140},
        #     "R1002;R2001": {"capacity": 120},
        #     "R1003;R2002": {"capacity": 70},
        #     "R2000;R3696": {"capacity": 120},
        #     "R2001;R3696": {"capacity": 120},
        #     "R2002;R3696": {"capacity": 120},
        #     "R1111;R1003": {"capacity": 100},
        #     "R1111;R4040": {"capacity": 100},
        #     "R4040;R2002": {"capacity": 100},
        # } 

        # example of traffic
        # flowTraffic = {
        #     "R1000;R3696": 120,
        #     "R1111;R3696": 100,
        # }
        
        edges = [(start, end) for start, end in (link.split(';') for link in links.keys())]
        graph = build_graph(edges)
        nodes = list(graph.keys())
        
        reachable_info = {}
        for node in graph:
            reachable_info[node] = find_reachable_nodes(graph, node, max_depth=1000)

        reachable_nodes = {node: info[0] for node, info in reachable_info.items()}
        reachable_edges = {node: info[1] for node, info in reachable_info.items()}

        #calculate how many values there are in total if you take into account all the flowTraffic and all the edges
        # total = 0
        # for flowTrafficKey in flowTraffic:
        #     flowTrafficKeySplit = flowTrafficKey.split(";")
        #     total += len(reachable_edges[flowTrafficKeySplit[0]])
       
        # print(f"before: {len(flowTraffic) * len(edges):,} ----> after: {total:,}")

        #calculate statistics for how big of a difference there is for each level of max_depth and write to file
        # depth_stats = []
        # for depth in range(1, 10):
        #     total = 0
        #     all_traffic_nodes_reachable = True
        #     for flowTrafficKey in flowTraffic:
        #         flowTrafficKeySplit = flowTrafficKey.split(";")
        #         reachable_nodes, reachable_edges = find_reachable_nodes(graph, flowTrafficKeySplit[0], max_depth=depth)
        #         #check if the endnode is reachable from the startnode with the given depth
        #         if flowTrafficKeySplit[1] not in reachable_nodes:
        #             all_traffic_nodes_reachable = False
        #         total += len(find_reachable_nodes(graph, flowTrafficKeySplit[0], max_depth=depth)[1])
        #     depth_stats.append([depth, total, all_traffic_nodes_reachable])
        #     print(f"depth: {depth}, total: {total:,}, all_traffic_nodes_reachable: {all_traffic_nodes_reachable}")
        # data = pd.DataFrame(depth_stats, columns=["depth", "total", "all_traffic_nodes_reachable"])
        # #format the data so ints are , separated
        # data["total"] = data["total"].apply(lambda x: f"{x:,}")
        # data.to_csv("depth_stats.csv", index=False, sep="\t")

        # #calculate how many traffic values make up 99% of the total traffic
        # # Calculate the total traffic
        # total_traffic = sum(flowTraffic.values())

        # # Sort the traffic values in descending order
        # sorted_flowTraffic = sorted(flowTraffic.items(), key=lambda item: item[1], reverse=True)

        # # Initialize a list to store the results
        # results = []

        # # Calculate the cutoff for each percentage from 50% to 100%
        # for percentage in range(50, 101):
        #     cutoff = total_traffic * (percentage / 100.0)
        #     cumulative_total = 0
        #     count = 0

        #     # Iterate over the sorted traffic values and accumulate the total
        #     for flowTrafficKey, value in sorted_flowTraffic:
        #         cumulative_total += value
        #         count += 1
        #         if cumulative_total >= cutoff:
        #             results.append((percentage, count))
        #             break

        # cutoff = total_traffic * 0.999
        # cumulative_total = 0
        # count = 0

        # # Iterate over the sorted traffic values and accumulate the total
        # for flowTrafficKey, value in sorted_flowTraffic:
        #     cumulative_total += value
        #     count += 1
        #     if cumulative_total >= cutoff:
        #         results.append((percentage, count))
        #         break

        

        # # Create a DataFrame from the results
        # df = pd.DataFrame(results, columns=['Percentage', 'Number of Traffic Values'])

        # # Write the DataFrame to a CSV file
        # df.to_csv('traffic_percentages.csv', index=False)

        # print(f"Data written to 'traffic_percentages.csv'.")

        return
 
        traffic = {}
        logger.info(f"processing traffic: {len(flowTraffic):,}")
        for flow in flowTraffic:
            split = flow.split(";")
            traffic[flow, split[0]] = flowTraffic[flow]
            traffic[flow, split[1]] = -flowTraffic[flow]


        utilization = m.addVars(links, vtype=gp.GRB.CONTINUOUS, name="Utilization")
        m.setObjective(
            gp.quicksum((utilization[link] ** 2 for link in links)),
            gp.GRB.MINIMIZE,
        )

        flowVars = m.addVars(flowTraffic.keys(), edges, name="flow")

        m.addConstrs((flowVars.sum("*", start, end) <= links[start+";"+end]["capacity"] for start, end in edges), "cap")

        m.addConstrs(
            (
                flowVars.sum(flow, "*", node) + traffic[flow, node] == flowVars.sum(flow, node, "*")
                if (flow, node) in traffic
                else flowVars.sum(flow, "*", node) == flowVars.sum(flow, node, "*")
                for flow in flowTraffic
                for node in nodes
            ),
            "flow",
        )

        # Constraints to set the flow through each link as the sum of flows for all traffic pairs
        for start, end in edges:
            linkFlow = gp.quicksum(flowVars[flow, start, end] 
                                   for flow in flowTraffic 
                                   if (flow, start, end) in flowVars)
            
            m.addConstr(
                linkFlow == utilization[f"{start};{end}"] * links[f"{start};{end}"]["capacity"],
                f"util_{start};{end}",
            )

        m.write("netflow.lp")
        m.optimize()

        # Example usage after optimization
        if m.Status == gp.GRB.OPTIMAL:
            solution = m.getAttr("X", flowVars)
            flow_values = {(flow, i, j): solution[flow, i, j] for flow in flowTraffic for i, j in edges if solution[flow, i, j] > 0}
            
            # Calculate ratios for all flows
            all_paths_with_ratios = calculate_ratios_for_all_flows(flow_values, flowTraffic, timestamp)
            
            print(all_paths_with_ratios)
            
            dataUtils.writeDataToFile(
                pd.DataFrame(
                    all_paths_with_ratios, columns=["timestamp", "flowName", "path", "ratio"]
                ),
                "ratioData",
                parserArgs,
            )
            
        return


def find_paths(flow_values, flowName, source, target):
    def recurse(node, path, flow):
        if node == target:
            return [(path, flow)]
        paths = []
        for (f_id, start, end), f in flow_values.items():
            if start == node and f_id == flowName:
                new_flow = min(flow, f) if flow is not None else f
                sub_paths = recurse(end, path + [end], new_flow)
                for sub_path, sub_flow in sub_paths:
                    if sub_flow > 0:
                        paths.append((sub_path, sub_flow))
        return paths

    return recurse(source, [source], None)


# Function to calculate ratios for all paths
def calculate_ratios_for_all_flows(flow_values, flowTraffic, timestamp):
    all_paths_with_ratios = []
    for flow_id, flow_amount in flowTraffic.items():
        source, target = flow_id.split(";")
        paths = find_paths(flow_values, flow_id, source, target)
        total_flow = sum(flow for _, flow in paths)
        # Ensure each path has its own flowName
        for path, flow in paths:
            all_paths_with_ratios.append([timestamp, flow_id, (';'.join(path)), flow / total_flow])        
    return all_paths_with_ratios
