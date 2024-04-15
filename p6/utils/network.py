from p6.network_model import Router, Link

def getRoutersHashFromFlows(flows):
    routersHash = {}
    for flow in flows:
        for path in flows[flow]:
            prevRouterName = ''
            for routerName in reversed(flows[flow][path]):
                if routerName not in routersHash:
                    routersHash[routerName] = Router(routerName)
                if prevRouterName != '':
                    routersHash[prevRouterName].addConnection(routersHash[routerName], False)
                    routersHash[routerName].addConnection(routersHash[prevRouterName], True)

                prevRouterName = routerName
    
    return routersHash

def recCalcRatios(links, currentRouter, linkCapacities):
    for ingressKey in currentRouter.ingress:
        newLink = Link(currentRouter.ingress[ingressKey].name, currentRouter.name, 0)
        newLink.capacity = linkCapacities[newLink.name]
        newLink.trafficRatio = internalCalcLinkRatio(links, currentRouter)
        links[newLink.name] = newLink
        recCalcRatios(links, currentRouter.ingress[ingressKey], linkCapacities)

def internalCalcLinkRatio(links, currentRouter):
    sumEgress = 0
    if currentRouter.name == 'G':
        sumEgress = 1
    else:
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
        print("")