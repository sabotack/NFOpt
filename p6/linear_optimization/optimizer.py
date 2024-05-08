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


def runLinearOptimizationModel(model, links, flows, traffic, timestamp, savelp=False):
    """
    Runs the linear optimization model to calculate the link utilization and the average link utilization.

    ### Parameters:
    ----------
    #### model: string
    The optimization model to run, can be 'averageUtilization', 'maxUtilization', or 'squaredUtilization'.

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

    with gp.Env(params=options) as env, gp.Model(env=env) as m:
        # Create optimization model based on the input model
        m = gp.Model("network_optimization", env=env)

        flowsWithPathNames = {}
        for sd in flows:
            flowsWithPathNames[sd] = []
            for pathNum in range(len(flows[sd])):
                #make array of path names into a single string seperated with ;s
                pathName = ";".join(flows[sd][pathNum])
                flowsWithPathNames[sd].append(pathName)

                
                

        # Decision variables for path ratios for each source-destination pair
        path_ratios = m.addVars(
            [(sd, flowsWithPathNames[sd][pathNum]) for sd in flows for pathNum in range(len(flows[sd]))],
            vtype=GRB.CONTINUOUS,
            name="PathRatios",
        )
        match model:
            case CalcType.AVERAGE.value:
                utilization = m.addVars(links, vtype=GRB.CONTINUOUS, name="Utilization")
                m.setObjective(
                    gp.quicksum(
                        (utilization[link] / links[link]["capacity"] for link in links)
                    ),
                    GRB.MINIMIZE,
                )
            case CalcType.MAX.value:
                max_utilization = m.addVar(vtype=GRB.CONTINUOUS, name="MaxUtilization")
                m.setObjective(max_utilization, GRB.MINIMIZE)
            case CalcType.SQUARED.value:
                utilization = m.addVars(links, vtype=GRB.CONTINUOUS, name="Utilization")
                m.setObjective(
                    gp.quicksum((utilization[link] ** 2 for link in links)),
                    GRB.MINIMIZE,
                )
            case _:
                raise ValueError(f"Invalid model: {model}")

        # Constraints for each link's utilization
        # Consists of the sum of ratios and traffic for each path related to the link
        for link in links:
            linkTuple = tuple((link[:5], link[5:]))
            link_flow = gp.quicksum(
                (
                    path_ratios[sd, flowsWithPathNames[sd][pathNum]] * traffic[sd]
                    if linkTuple in zip(flows[sd][pathNum][:-1], flows[sd][pathNum][1:])
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
                        link_flow == utilization[link] * links[link]["capacity"],
                        name=f"util_{link}",
                    )
                case _:
                    raise ValueError(f"Invalid model: {model}")

        for sd in traffic:
            m.addConstr(path_ratios.sum(sd, "*") == 1, name=f"traffic_split_{sd}")

        if savelp:
            if not os.path.exists(OPT_MODELS_OUTPUT_DIR):
                os.makedirs(OPT_MODELS_OUTPUT_DIR)

            ts = datetime.now().strftime("%Y%m%d")
            time = (timestamp[:3] + timestamp[4:-6]).lower()
            m.write(f"{OPT_MODELS_OUTPUT_DIR}/{ts}_{model}_{time}.lp")

        logger.info("Started optimization...")
        m.optimize()
        logger.info("Finished optimization")

        # Output the results
        ratioData = []
        if m.status == GRB.OPTIMAL:
            # debug and save optimal path ratios
            for sd in flows:
                logger.debug(f"Optimal path ratios for {sd}:")
                for pathNum in range(len(flowsWithPathNames[sd])):
                    ratioData.append(
                        [timestamp, sd, flowsWithPathNames[sd][pathNum], path_ratios[sd, flowsWithPathNames[sd][pathNum]].x]
                    )
                    logger.debug(
                        f"   Path {pathNum}: {path_ratios[sd, flowsWithPathNames[sd][pathNum]].x * 100} %"
                    )

            dataUtils.writeDataToFile(
                pd.DataFrame(
                    ratioData, columns=["timestamp", "flowName", "path", "ratio"]
                ),
                model,
                True,
            )

            # Calculate average, min and max link utilization
            totalLinkUtil = 0
            minLinkUtil = 0
            maxLinkUtil = 0
            for link in links:
                linkTuple = tuple((link[:5], link[5:]))
                link_flow = sum(
                    (
                        path_ratios[sd, flowsWithPathNames[sd][pathNum]].x * traffic[sd]
                        if linkTuple
                        in zip(flows[sd][pathNum][:-1], flows[sd][pathNum][1:])
                        else 0
                    )
                    for sd in links[link]["listFlows"]
                    for pathNum in range(len(flowsWithPathNames[sd]))
                )
                totalLinkUtil += link_flow / links[link]["capacity"] * 100

                # Update min and max link utilization
                if (link_flow / links[link]["capacity"] * 100) < minLinkUtil:
                    minLinkUtil = link_flow / links[link]["capacity"] * 100
                if (link_flow / links[link]["capacity"] * 100) > maxLinkUtil:
                    maxLinkUtil = link_flow / links[link]["capacity"] * 100

            avgLinkUtil = totalLinkUtil / len(links)
            logger.info(f"Average link utilization: {avgLinkUtil}% for model {model}")

            return avgLinkUtil, minLinkUtil, maxLinkUtil

        elif m.status == GRB.INFEASIBLE:
            logger.error("Model is infeasible")
            m.computeIIS()
            logger.error("The following constraints cannot be satisfied:")
            for c in m.getConstrs():
                if c.IISConstr:
                    logger.error(c.constrName)
        else:
            logger.error("Optimization ended with status %d" % m.status)
