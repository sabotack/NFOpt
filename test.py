from datetime import datetime
import os
import pandas as pd
import gurobipy as gp
import argparse

from gurobipy import GRB
from dotenv import load_dotenv

from p6.calc_type_enum import CalcType
from p6.utils import log
from p6.utils import data as dataUtils

logger = log.setupCustomLogger(__name__)

load_dotenv("variables.env")

DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR")
OPT_MODELS_OUTPUT_DIR = "optimization_models"

# Environment gurobi license variables
options = {
    "WLSACCESSID": os.getenv("WLSACCESSID"),
    "WLSSECRET": os.getenv("WLSSECRET"),
    "LICENSEID": int(os.getenv("LICENSEID")),
}


def runLinearOptimizationModel(
    parserArgs, links, flows, traffic, timestamp, savelp=True
):
    """
    Runs the linear optimization model to calculate the link utilization and the average link utilization.

    ### Parameters:
    ----------
    #### model: string
    The optimization model to run, can be 'averageUtilization', 'maxUtilization', or 'squared'.

    #### links: dict
    The links in the network, indexed by linkName.

    #### paths: dict
    The paths for each source-destination pair, with the paths split into a list of paths.

    #### traffic: dict
    The traffic for each source-destination pair.

    ### Returns:
    ----------
    The total link utilization, the average link utilization, and the link utilization for each link.
    """
    logger.info("Started running linear optimization model...")
    model = CalcType.SQUARED.value

    # example of link data
    # links = {
    #     "A;B": {"capacity": 100, "listFlows": ["A;G"]},
    #     "A;C": {"capacity": 80, "listFlows": ["A;G"]},
    #     "B;D": {"capacity": 140, "listFlows": ["A;G"]},
    #     "B;E": {"capacity": 120, "listFlows": ["A;G"]},
    #     "C;F": {"capacity": 70, "listFlows": ["A;G", "X;G"]},
    #     "D;G": {"capacity": 120, "listFlows": ["A;G"]},
    #     "E;G": {"capacity": 120, "listFlows": ["A;G"]},
    #     "F;G": {"capacity": 120, "listFlows": ["A;G", "X;G"]},
    #     "X;C": {"capacity": 100, "listFlows": ["X;G"]},
    #     "X;Y": {"capacity": 100, "listFlows": ["X;G"]},
    #     "Y;F": {"capacity": 100, "listFlows": ["X;G"]},
    # }

    # flows = {
    #     "A;G": ['A;B;D;G', 'A;B;E;G', 'A;C;F;G'],
    #     "X;G": ['X;C;F;G', 'X;Y;F;G'],
    # }

    # traffic = {
    #     "A;G": 50,
    #     "X;G": 75,
    # }

    links = {
        "A;B": {"capacity": 100, "listFlows": ["A;G"]},
        "A;C": {"capacity": 100, "listFlows": ["A;G"]},
        "B;D": {"capacity": 100, "listFlows": ["A;G"]},
        "B;E": {"capacity": 100, "listFlows": ["A;G"]},
        "C;F": {"capacity": 100, "listFlows": ["A;G"]},
        "D;G": {"capacity": 100, "listFlows": ["A;G"]},
        "E;G": {"capacity": 100, "listFlows": ["A;G"]},
        "F;G": {"capacity": 100, "listFlows": ["A;G"]},
    }
    flows = {
        "A;G": ['A;B;D;G', 'A;B;E;G', 'A;C;F;G'],
    }

    traffic = {
        "A;G": 100,
    }


    with gp.Env(params=options) as env, gp.Model(env=env) as m:
        # Create optimization model based on the input model
        m = gp.Model("network_optimization", env=env)

        # Decision variables for path ratios for each source-destination pair
        path_ratios = m.addVars(
            [
                (sd, flows[sd][pathNum])
                for sd in flows
                for pathNum in range(len(flows[sd]))
            ],
            vtype=GRB.CONTINUOUS,
            name="PathRatios",
        )
        match model:
            case CalcType.AVERAGE.value:
                utilization = m.addVars(links, vtype=GRB.CONTINUOUS, name="Utilization")
                m.setObjective(
                    gp.quicksum(
                        (utilization[link] for link in links)
                    ),
                    GRB.MINIMIZE,
                )
            case CalcType.MAX.value:
                max_utilization = m.addVar(vtype=GRB.CONTINUOUS, name="MaxUtilization")
                m.setObjective(max_utilization, GRB.MINIMIZE)
            case CalcType.SQUARED.value:
                utilization = m.addVars(links, vtype=GRB.CONTINUOUS, name="Utilization")
                # make the objective function
                quadObjective = sum(utilization[link] * utilization[link] for link in links)
                m.setObjective(quadObjective, GRB.MINIMIZE)
            case _:
                raise ValueError(f"Invalid model: {model}")

        # Constraints for each link's utilization
        # Consists of the sum of ratios and traffic for each path related to the link
        for link in links:
            link_flow = gp.quicksum(
                (
                    path_ratios[sd, flows[sd][pathNum]] * traffic[sd]
                    if link in flows[sd][pathNum]
                    else 0
                )
                for sd in links[link]["listFlows"]
                for pathNum in range(len(flows[sd]))
            )

            m.addConstr(link_flow <= links[link]["capacity"], name=f"cap_{link}")

            match model:
                case CalcType.AVERAGE.value:
                    m.addConstr(
                        link_flow == links[link]["capacity"] * utilization[link],
                        name=f"util_{link}",
                    )
                case CalcType.MAX.value:
                    m.addConstr(
                        link_flow / links[link]["capacity"] <= max_utilization,
                        name=f"util_{link}",
                    )
                case CalcType.SQUARED.value:
                    m.addConstr(
                        link_flow == links[link]["capacity"] * utilization[link],
                        name=f"util_{link}",
                    )
                case _:
                    raise ValueError(f"Invalid model: {model}")

        for sd in traffic:
            m.addConstr(path_ratios.sum(sd, "*") == 1, name=f"traffic_split_{sd}")

        if savelp:
            ts = datetime.now().strftime("%Y%m%d")
            time = (timestamp[:3] + timestamp[4:-6]).lower()
            m.write(f"{model}_for_emulio.lp")

        logger.info("Started optimization...")
        m.optimize()
        logger.info("Finished optimization")

        # Output the results
        ratioData = []
        if m.status == GRB.OPTIMAL:
            print("HEEERES")
            # debug and save optimal path ratios
            for sd in flows:
                print("here")
                logger.debug(f"Optimal path ratios for {sd}:")
                for pathNum in range(len(flows[sd])):
                    ratioData.append(
                        [
                            timestamp,
                            sd,
                            flows[sd][pathNum],
                            path_ratios[sd, flows[sd][pathNum]].x,
                        ]
                    )
                    logger.info(
                        f"   Path {pathNum}: {path_ratios[sd, flows[sd][pathNum]].x * 100} %"
                    )
            #calculate link utilization over every link
            for link in links:
                link_flow = sum(
                    (
                        path_ratios[sd, flows[sd][pathNum]].x * traffic[sd]
                        if link in flows[sd][pathNum]
                        else 0
                    )
                    for sd in links[link]["listFlows"]
                    for pathNum in range(len(flows[sd]))
                )
                logger.info(f"Link {link} utilization: {link_flow / links[link]['capacity'] * 100} %")
    

            #print to file
            df = pd.DataFrame(ratioData, columns=["timestamp", "sd", "path", "ratio"])
            df.to_csv(f"test.csv", index=False)

            # Calculate link utilization
            utils = {}

            for link in links:
                link_flow = sum(
                    (
                        path_ratios[sd, flows[sd][pathNum]].x * traffic[sd]
                        if link in flows[sd][pathNum]
                        else 0
                    )
                    for sd in links[link]["listFlows"]
                    for pathNum in range(len(flows[sd]))
                )

                utils[link] = link_flow / links[link]["capacity"] * 100

            return utils
        elif m.status == GRB.INFEASIBLE:
            logger.error("Model is infeasible")
            m.computeIIS()
            logger.error("The following constraints cannot be satisfied:")
            for c in m.getConstrs():
                if c.IISConstr:
                    logger.error(c.constrName)
        else:
            logger.error("Optimization ended with status %d" % m.status)

runLinearOptimizationModel(None, None, None, None, "Tue 00:00:00", True)

