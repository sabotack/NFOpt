import gurobipy as gp
from gurobipy import GRB

import pandas as pd


def readCsvDataFile(filename, numLines, columnNames = [], skipLines = 0):
    data = pd.read_csv(filename, skiprows=skipLines, nrows=numLines, names=columnNames)
    return data



def main():
    routers = readCsvDataFile('../dataset-week/routers.csv', 10, ['router', 'latitude', 'longitude', 'type'], 1)
    links = readCsvDataFile('../dataset-week/links.csv', 10, ['linkStart', 'linkEnd', 'capacity'], 1)
    traffic = readCsvDataFile('../dataset-week/flow-traffic-day1.csv', 10, ['timestamp', 'trafficStart', 'trafficEnd', 'traffic'])

    print(routers)
    print(traffic)
    print(links)