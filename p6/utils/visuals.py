import matplotlib.pyplot as plt
import pandas as pd
import os
from p6.utils import log

logger = log.setupCustomLogger(__name__)
DATE = os.getenv("DATE")

def plotAllData():
    baseline = pd.read_csv(f'./output/{DATE}_baseline.csv')
    averageUtilization = pd.read_csv(f'./output/{DATE}_averageUtilization.csv')
    maxUtilization = pd.read_csv(f'./output/{DATE}_maxUtilization.csv')
    squaredUtilization = pd.read_csv(f'./output/{DATE}_squaredUtilization.csv')

    # Plot a graph over avgUtil from each optimization model and baseline
    plt.plot(baseline['avg_util'], label='Base')
    plt.plot(averageUtilization['avg_util'], label='Avg Util')
    plt.plot(maxUtilization['avg_util'], label='Max Util')
    plt.plot(squaredUtilization['avg_util'], label='Sqr Util')
    plt.xlabel('Timestamp')
    plt.ylabel('Average Utilization (%)')
    plt.legend()
    plt.show()

    # Plot a graph over maxUtil from each optimization model and baseline
    plt.plot(baseline['max_util'], label='MU Base', linestyle='--')
    plt.plot(averageUtilization['max_util'], label='MU Avg Util', linestyle='--')
    plt.plot(maxUtilization['max_util'], label='MU Max Util', linestyle='--')
    plt.plot(squaredUtilization['max_util'], label='MU Sqr Util', linestyle='--')
    plt.xlabel('Timestamp')
    plt.ylabel('Max Utilization (%)')
    plt.legend()
    plt.show()
    
