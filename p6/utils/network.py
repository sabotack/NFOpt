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
