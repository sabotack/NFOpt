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

        # flowTraffic = {
        #     "R1000;R3696": 120,
        #     "R1111;R3696": 100,
        # }

        # flowTraffic = {
        #     "A;G": 100,
        #     "X;G": 100,
        # }

        m.setParam("logFile", "gurobi.log")

        nodes = []
        edges = []
        for link in links:
            split = link.split(";")
            edges.append((split[0], split[1]))

            if split[0] not in nodes:
                nodes.append(split[0]) 
            if split[1] not in nodes:
                nodes.append(split[1])

        traffic = {}

        sorted_flowTraffic = sorted(flowTraffic.items(), key=lambda item: item[1], reverse=True)
        total_demand = sum(flowTraffic.values())
        percentage = 0.75
        demand_threshold = total_demand * percentage
        cumulative_demand = 0
        significant_flowTraffic = {}
        for flow, value in sorted_flowTraffic:
            if cumulative_demand <= demand_threshold:
                significant_flowTraffic[flow] = value
                cumulative_demand += value
            else:
                break  # Stop adding values once the threshold is reached
        
        for flow in significant_flowTraffic:
            split = flow.split(";")
            traffic[flow, split[0]] = significant_flowTraffic[flow]
            traffic[flow, split[1]] = -significant_flowTraffic[flow]

        utilization = m.addVars(links, vtype=gp.GRB.CONTINUOUS, name="Utilization")
        m.setObjective(
            gp.quicksum((utilization[link] ** 2 for link in links)),
            gp.GRB.MINIMIZE,
        )

        logger.info(f"adding vars for flow: {len(significant_flowTraffic):,} and edges: {len(edges):,} so {len(significant_flowTraffic) * len(edges):,} flowVars in total")

        flowVars = m.addVars(significant_flowTraffic.keys(), edges, name="flow")

        logger.info(f"adding capacity constraints for {len(edges):,} edges")

        m.addConstrs((flowVars.sum("*", start, end) <= links[start+";"+end]["capacity"] for start, end in edges), "cap")

        logger.info(f"adding flow constraints for {len(significant_flowTraffic):,} flows and {len(nodes):,} nodes")

        m.addConstrs(
            (
                flowVars.sum(flow, "*", node) + traffic[flow, node] == flowVars.sum(flow, node, "*")
                if (flow, node) in traffic
                else flowVars.sum(flow, "*", node) == flowVars.sum(flow, node, "*")
                for flow in significant_flowTraffic
                for node in nodes
            ),
            "flow",
        )

        logger.info(f"adding utilization constraints for {len(edges):,} edges")

        # Constraints to set the flow through each link as the sum of flows for all traffic pairs
        for start, end in edges:
            linkFlow = gp.quicksum(flowVars[flow, start, end] 
                                   for flow in significant_flowTraffic 
                                   if (flow, start, end) in flowVars)
            
            m.addConstr(
                linkFlow == utilization[f"{start};{end}"] * links[f"{start};{end}"]["capacity"],
                f"util_{start};{end}",
            )

        m.write("netflow.lp")
        m.optimize()

    # Define the threshold percentage (e.g., 10%)
    threshold_percentage = 0.001

    if m.Status == gp.GRB.OPTIMAL:
        solution = m.getAttr("X", flowVars)
        flow_values = {(flow, i, j): solution[flow, i, j] for flow in significant_flowTraffic for i, j in edges if solution[flow, i, j] > 0}

        unique_flows = set()

        # New dictionary to hold the threshold values for each flow
        threshold_values = {flow: flowTraffic[flow] * threshold_percentage for flow in flowTraffic}

        new_flow_values = {}
        for (flow, start, end), value in flow_values.items():
            # Get the threshold value for the current flow
            current_threshold_value = threshold_values[flow]
            
            # Compare each flow value with its corresponding threshold value
            if value >= current_threshold_value:
                # Check if the flow is unique and print it
                if flow not in unique_flows:
                    unique_flows.add(flow)
                new_flow_values[(flow, start, end)] = value

        logger.info(f"Flows before: {len(significant_flowTraffic)}")
        logger.info(f"Flows after: {len(unique_flows)}")

        flow_values = new_flow_values

        # Calculate ratios for all flows
        #calculate time taken to calculate ratios
        startTime = pd.Timestamp.now()
        all_paths_with_ratios = calculate_ratios_for_all_flows(flow_values, significant_flowTraffic, timestamp)
        endTime = pd.Timestamp.now()

        logger.info(f"Time taken to calculate ratios: {endTime - startTime}")

        dataUtils.writeDataToFile(
            pd.DataFrame(
                all_paths_with_ratios, columns=["timestamp", "flowName", "path", "ratio"]
            ),
            "ratioData",
            parserArgs,
        )
        
    return


def find_paths(flow_values, flowName, source, target):
    paths = []
    queue = deque([(source, [source], float('inf'))])
    visited = set()
    i = 0
    while queue:
        i+=1
        if i % 10000 == 0:
            logger.info(f"processed {i:,} paths out of {len(queue):,} remaining")
        node, path, flow = queue.popleft()


        if (node, flow) in visited:
            continue
        visited.add((node, flow))

        if node == target:
            paths.append((path, flow))
            continue

        for (flow_id, start, end), f in flow_values.items():
            if start == node and flow_id == flowName and (end, f) not in visited:
                new_flow = min(flow, f)
                if new_flow > 0:
                    queue.append((end, path + [end], new_flow))

    return paths


# Function to calculate ratios for all paths
def calculate_ratios_for_all_flows(flow_values, flowTraffic, timestamp):
    all_paths_with_ratios = []
    i = 0
    for flow_id, flow_amount in flowTraffic.items():
        i += 1
        if i % 5000 == 0:
            logger.info(f"processed {i:,} flows out of {len(flowTraffic):,} remaining")
        source, target = flow_id.split(";")
        paths = find_paths(flow_values, flow_id, source, target)
        total_flow = sum(flow for _, flow in paths)
        # Ensure each path has its own flowName
        for path, flow in paths:
            all_paths_with_ratios.append([timestamp, flow_id, (';'.join(path)), flow / total_flow])     
    return all_paths_with_ratios