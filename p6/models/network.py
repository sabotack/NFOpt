class Router:
    def __init__(self, name):
        self.name = name
        self.ingress = {}
        self.egress = {}
        self.paths = []

    def addConnection(self, link, isEgress):
        if isEgress:
            self.egress[link.name] = link
        else:
            self.ingress[link.name] = link

    def addPath(self, path):
        self.paths.append(path)


class Link:
    def __init__(self, linkStart, linkEnd, capacity):
        self.linkStart = linkStart
        self.linkEnd = linkEnd
        self.capacity = capacity
        self.name = f"{linkStart}{linkEnd}"
        self.trafficRatio = 0
