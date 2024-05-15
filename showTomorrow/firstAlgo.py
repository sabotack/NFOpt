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

def find_reachable_nodes(graph, edges, source):
    visited = set()
    queue = deque([source])
    reachable_nodes = set()

    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            reachable_nodes.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
    return reachable_nodes

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
        
        reachable_nodes = {}
        for node in graph:
            reachable_nodes[node] = find_reachable_nodes(graph, edges, node)
    
        #calculate how many values there are in total if you take into account all the flowTraffic and all the edges
        total = 0
        for flowTrafficKey in flowTraffic:
            flowTrafficKeySplit = flowTrafficKey.split(";")
            total += len(reachable_nodes[flowTrafficKeySplit[0]])
            total += 1
        print(f"before: {len(flowTraffic) * len(edges):,} ----> after: {total:,}")
        print("wow, very cool 😳 😳")
        
        print(find_reachable_nodes(graph, edges, "R1004"))
        print(len(find_reachable_nodes(graph, edges, "R1004")))

        return 
    

        #calculate how many values there are in total
        total = 0
        for node in reachable_nodes:
            total += len(reachable_nodes[node])
            total += 1 # for the node itself
        
        print(total)

        nodes = []
        edges = []
        logger.info(f"processing links: {len(links):,}")
        for link in links:
            split = link.split(";")
            edges.append((split[0], split[1]))

            if split[0] not in nodes:
                nodes.append(split[0]) 
            if split[1] not in nodes:
                nodes.append(split[1])

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


        logger.info(f"processing flowVars: {(len(flowTraffic) * len(edges)):,}")
        logger.info("crazy that its so much!!11 😳 😳")
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
