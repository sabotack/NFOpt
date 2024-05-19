import os
import sys
import pandas as pd
import multiprocessing as mp

from p6.utils import log
from functools import partial
from datetime import datetime
from dotenv import load_dotenv
from matplotlib import pyplot as plt

load_dotenv("variables.env")
logger = log.setupCustomLogger(__name__)

DATASET_PATH = os.getenv("DATASET_PATH")
DATASET_PATHS_PREFIX = os.getenv("DATASET_PATHS_PREFIX")
DATASET_TRAFFIC_PREFIX = os.getenv("DATASET_TRAFFIC_PREFIX")
DATASET_LINKS_NAME = os.getenv("DATASET_LINKS_NAME")

DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR")
RATIOS_DIR_NAME = "ratios"
LINKS_DIR_NAME = "links"

dayNum = 2
date = "20240517"
type = "squared"


# Assuming the data is in CSV format and stored in 'data1.csv' and 'data2.csv'
data1 = pd.read_csv(f"{DATA_OUTPUT_DIR}/day{dayNum}/{date}_{type}.csv"),
data2 = pd.read_csv(f"{DATA_OUTPUT_DIR}/day{dayNum}/{date}_{type}.csv"),

# Convert timestamps to a format that can be easily plotted
data1['timestamp'] = pd.to_datetime(data1['timestamp'], format='Wed %H:%M:%S').dt.time
data2['timestamp'] = pd.to_datetime(data2['timestamp'], format='Wed %H:%M:%S').dt.time

# Plotting the data
plt.figure(figsize=(10, 5))

# Plot min_util
plt.plot(data1['timestamp'], data1['min_util'], label='Min Util File 1', marker='o')
plt.plot(data2['timestamp'], data2['min_util'], label='Min Util File 2', marker='o')

# Plot max_util
plt.plot(data1['timestamp'], data1['max_util'], label='Max Util File 1', marker='s')
plt.plot(data2['timestamp'], data2['max_util'], label='Max Util File 2', marker='s')

# Plot avg_util
plt.plot(data1['timestamp'], data1['avg_util'], label='Avg Util File 1', linestyle='--')
plt.plot(data2['timestamp'], data2['avg_util'], label='Avg Util File 2', linestyle='--')

# Adding labels and title
plt.xlabel('Timestamp')
plt.ylabel('Utilization')
plt.title('Comparison of Utilization Data')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

# Show the plot
plt.show()
