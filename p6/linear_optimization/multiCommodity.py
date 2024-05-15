from datetime import datetime
import os
import pandas as pd
import gurobipy as gp

from gurobipy import GRB
from dotenv import load_dotenv

from p6.calc_type_enum import CalcType
from p6.utils import log
from p6.utils import data as dataUtils

logger = log.setupCustomLogger(__name__)

load_dotenv("variables.env")

OPT_MODELS_OUTPUT_DIR = os.getenv("OPT_MODELS_OUTPUT_DIR")

# Environment gurobi license variables
options = {
    "WLSACCESSID": os.getenv("WLSACCESSID"),
    "WLSSECRET": os.getenv("WLSSECRET"),
    "LICENSEID": int(os.getenv("LICENSEID")),
}


def runMultiCommodityOptimizer(links, traffic, timestamp):
    # Assuming 'options' is defined and contains Gurobi environment options
    with gp.Env(params=options) as env:
        m = gp.Model("multi_commodity_network_flow", env=env)
        #add log file for gurobi
        m.setParam('LogFile', f"tempLogFile_{timestamp}.log")

        # Define nodes based on the unique endpoints in links
        nodes = set()
        for link in links.values():
            nodes.update([link['linkStart'], link['linkEnd']])

        # Define arcs based on the links
        arcs = {(link['linkStart'], link['linkEnd']): link['capacity'] for link in links.values()}
        print("HERE 1")

        # Define commodities based on the unique source-destination pairs in traffic
        commodities = set(traffic.values())
        print("HERE 2")


        #print out the flow
        for k in commodities:
            for i, j in arcs:
                print(f"flow_{k}_{i}_{j}")
                print(flow[k, i, j])

        # Decision variables for flow on arc (i, j) for commodity k
        flow = m.addVars(commodities, arcs.keys(), vtype=GRB.CONTINUOUS, name="flow")
        print("HERE 3")

        # Objective: Minimize the sum of flows (can be adapted to include costs if available)


        m.setObjective(gp.quicksum(flow[k, i, j] for k in commodities for i, j in arcs), GRB.MINIMIZE)
        print("HERE 4")

        # Capacity constraints for each arc
        for (i, j), capacity in arcs.items():
            m.addConstr(sum(flow[k, i, j] for k in commodities) <= capacity, name=f"cap_{i}_{j}")

        print("HERE 5")

        # Flow conservation constraints for each commodity at each node
        for k in commodities:
            # for every 10000 flows of commoity k, write the current status
            if k % 10000 == 0:
                print(f"Commodity {k} out of {len(commodities)}")
            for j in nodes:
                inflow = gp.quicksum(flow[k, i, j] for i, _, j in arcs if (i, j) in arcs)
                outflow = gp.quicksum(flow[k, j, i] for j, _, i in arcs if (j, i) in arcs)
                # Demand is the net flow required at node j for commodity k
                demand = traffic.get(k, {}).get(j, 0)
                m.addConstr(inflow - outflow == demand, name=f"node_{j}_com_{k}")

        # Solve the model
        m.write(f"multi_commodity_network_flow_{timestamp}.lp")
        m.optimize()
        

        # Process the results
        if m.status == GRB.OPTIMAL:
            solution = m.getAttr('X', flow)
            for k in commodities:
                print(f"Commodity {k}:")
                for i, j in arcs:
                    if solution[k, i, j] > 0:
                        print(f"  Flow from {i} to {j}: {solution[k, i, j]}")
        else:
            print("No solution found")