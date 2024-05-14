import os
import gurobipy as gp

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

# def test():
def optMC(links, flowTraffic):
    with gp.Env(params=options) as env, gp.Model(env=env) as m:
        m = gp.Model("netflow", env=env)

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
        
        # flowTraffic = {
        #     "A;G": 120,
        #     "X;G": 100,
        # }

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

        # Print solution
        if m.Status == gp.GRB.OPTIMAL:
            solution = m.getAttr("X", flowVars)
            for flow in flowTraffic:
                print(f"\nOptimal paths for {flow}:")
                for i, j in edges:
                    if solution[flow, i, j] > 0:
                        print(f"{i} -> {j}: {solution[flow, i, j]:g}")

# def optMC():
def works():

    # links = dataUtils.readLinks()
    # traffic = dataUtils.readTraffic(2)

    with gp.Env(params=options) as env, gp.Model(env=env) as m:
        m = gp.Model("netflow", env=env)

        # Base data
        commodities = ["Traffic1", "Traffic2"]
        nodes = ["A", "B", "C", "D", "E", "F", "G", "X", "Y"]

        arcs, capacity = gp.multidict(
            {
                ("A", "B"): 100,
                ("A", "C"): 80,
                ("B", "D"): 140,
                ("B", "E"): 120,
                ("C", "F"): 70,
                ("D", "G"): 120,
                ("E", "G"): 120,
                ("F", "G"): 120,
                ("X", "C"): 100,
                ("X", "Y"): 100,
                ("Y", "F"): 100,
            }
        )

        # Supply (> 0) and demand (< 0) for pairs of commodity-city
        inflow = {
            ("Traffic1", "A"): 120,
            ("Traffic1", "G"): -120,
            ("Traffic2", "X"): 100,
            ("Traffic2", "G"): -100,
        }

        # Create optimization model
        m = gp.Model("netflow")

        utilization = m.addVars(arcs, vtype=gp.GRB.CONTINUOUS, name="Utilization")
        m.setObjective(
            gp.quicksum((utilization[link] ** 2 for link in arcs)),
            gp.GRB.MINIMIZE,
        )

        # Create variables
        flow = m.addVars(commodities, arcs, name="flow")
        
        # Arc-capacity constraints
        m.addConstrs((flow.sum("*", i, j) <= capacity[i, j] for i, j in arcs), "cap")

        # Equivalent version using Python looping
        # for i, j in arcs:
        #   m.addConstr(sum(flow[h, i, j] for h in commodities) <= capacity[i, j],
        #               "cap[%s, %s]" % (i, j))


        # Flow-conservation constraints
        m.addConstrs(
            (
                flow.sum(h, "*", j) + inflow[h, j] == flow.sum(h, j, "*")
                if (h, j) in inflow
                else flow.sum(h, "*", j) == flow.sum(h, j, "*")
                for h in commodities
                for j in nodes
            ),
            "node",
        )

        m.write("netflow2.lp")

        # Alternate version:
        # m.addConstrs(
        #   (gp.quicksum(flow[h, i, j] for i, j in arcs.select('*', j)) + inflow[h, j] ==
        #     gp.quicksum(flow[h, j, k] for j, k in arcs.select(j, '*'))
        #     for h in commodities for j in nodes), "node")

        # Compute optimal solution
        m.optimize()

        # Print solution
        if m.Status == gp.GRB.OPTIMAL:
            solution = m.getAttr("X", flow)
            for h in commodities:
                print(f"\nOptimal flows for {h}:")
                for i, j in arcs:
                    if solution[h, i, j] > 0:
                        print(f"{i} -> {j}: {solution[h, i, j]:g}")