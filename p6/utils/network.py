import os
from p6.models.network import Router, Link

from p6.utils import log

logger = log.setupCustomLogger(__name__)

import configparser

config = configparser.ConfigParser()
config.read("config.ini")

from dotenv import load_dotenv

load_dotenv("variables.env")

AVG_CAPACITY = int(os.getenv("AVERAGE_CAPACITY"))


def getRoutersHashFromFlow(flow):
    """
    This function creates a hash of routers from a list of paths.

    ### Parameters
    ----------
    #### flow : list
        A list of paths. Each path is a list of routers.

    ### Returns
    ----------
    A hash of routers for the specific flow.
    """

    routersHash = {}

    for path in flow:
        pathStr = ";".join(path)
        prevRouterName = ""

        # Go through the routers in the path in reverse to get the correct order of routers
        for routerName in reversed(path):
            if routerName not in routersHash:
                routersHash[routerName] = Router(routerName)

            # Add the current path string to the router if it does not exist in the array
            if pathStr not in routersHash[routerName].paths:
                routersHash[routerName].addPath(pathStr)

            if prevRouterName != "":
                routersHash[prevRouterName].addConnection(
                    routersHash[routerName], isEgress=False
                )
                routersHash[routerName].addConnection(
                    routersHash[prevRouterName], isEgress=True
                )

            prevRouterName = routerName

    return routersHash


def getFlowLinks(routers, capacities, ratios):
    """
    This function creates a hash of links from routers by traversing breadth-first, and calculates the traffic ratio for each link.

    ### Parameters
    ----------
    #### routers : dict
        A hash of routers for a specific flow.
    #### capacities : dict
        A hash of capacities for each link.

    ### Returns
    ----------
    A hash of links.
    """

    (startRouter, endRouter) = _getEndRouter(routers)
    flowName = startRouter.name + endRouter.name
    flowLinks = {}
    visited = []
    queue = []

    visited.append(endRouter)
    queue.append(endRouter)

    logger.debug(f"Started traversing (endrouter: {endRouter.name})")

    while queue:
        currentRouter = queue.pop(0)

        for ingressKey in currentRouter.ingress:
            newLink = Link(
                currentRouter.ingress[ingressKey].name, currentRouter.name, 0
            )

            if newLink.name not in capacities:
                newLink.capacity = AVG_CAPACITY
            else:
                newLink.capacity = capacities[newLink.name]["capacity"]

            if currentRouter == endRouter:
                newLink.trafficRatio = 0
                if ratios is not None:
                    for path in currentRouter.ingress[ingressKey].paths:
                        # logger.info(f"Found ratio for {flowName} {path}")
                        newLink.trafficRatio += float(ratios[flowName, path])
                else:
                    newLink.trafficRatio = 1 / len(currentRouter.ingress)
            else:
                newLink.trafficRatio = _calcLinkRatio(flowLinks, currentRouter)

            flowLinks[newLink.name] = newLink

            if currentRouter.ingress[ingressKey] not in visited:
                visited.append(currentRouter.ingress[ingressKey])
                queue.append(currentRouter.ingress[ingressKey])

    logger.debug(f"Finished traversing (endrouter: {endRouter.name})")

    return flowLinks


def _getEndRouter(routers):
    """
    Internal function to get the end router of a network.

    ### Parameters
    ----------
    #### routers : dict
        A hash of routers.
    """

    startRouter = None
    endRouter = None

    for routerKey in routers:
        if len(routers[routerKey].egress) == 0:
            endRouter = routers[routerKey]
        if len(routers[routerKey].ingress) == 0:
            startRouter = routers[routerKey]

    return (startRouter, endRouter)


def _calcLinkRatio(links, currentRouter):
    """
    Internal function to calculate the traffic ratio for a link.

    ### Parameters
    ----------
    #### links : dict
        A hash of links.
    #### currentRouter : Router
        The current router.
    """

    sumEgress = 0
    for linkKey in links:
        if links[linkKey].linkStart == currentRouter.name:
            sumEgress += links[linkKey].trafficRatio

    return sumEgress / len(currentRouter.ingress)


def printRouterHash(routersHash):
    for routerKey in routersHash:
        print(f"Router: {routerKey}")
        for ingressKey in routersHash[routerKey].ingress:
            print(f"-Ingress:{routersHash[routerKey].ingress[ingressKey].name}")
        for egressKey in routersHash[routerKey].egress:
            print(f"-Egress:{routersHash[routerKey].egress[egressKey].name}")
        for path in routersHash[routerKey].paths:
            print(f"-Path:{path}")
        print("")
