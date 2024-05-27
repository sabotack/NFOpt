from p6.utils import log

logger = log.setupCustomLogger(__name__)


def getLinksFromFlow(flow):
    links = []

    for path in flow:
        pathRouters = path.split(";")
        for i in range(len(pathRouters) - 1):
            linkName = pathRouters[i] + ";" + pathRouters[i + 1]
            if linkName not in links:
                links.append(linkName)

    return links


def getLinksFromPath(path_str):
    """
    Given a path as a string of nodes separated by semicolons, return a list of link strings representing the connections between the nodes.

    Example:
    Input: 'R1004;R1993;R1321;R1010'
    Output: ['R1004;R1993', 'R1993;R1321', 'R1321;R1010']
    """
    # Split the path string into a list of nodes
    nodes = path_str.split(";")
    # Create links as strings of consecutive nodes separated by a semicolon
    links = [nodes[i] + ";" + nodes[i + 1] for i in range(len(nodes) - 1)]
    return links
