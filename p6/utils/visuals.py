import matplotlib.pyplot as plt
import pandas as pd
import os
from p6.utils import log

logger = log.setupCustomLogger(__name__)


def plotAllData():
    try:
        for file in os.listdir("./output"):
            if file.endswith(".csv"):
                logger.info(f"Plotting data from {file}")
                data = pd.read_csv(f"./output/{file}")
                plt.plot(data["avg_util"], label=file[9:-4])
        plt.xlabel("Timestamp")
        plt.ylabel("Average Utilization (%)")
        plt.legend()
        plt.show()
    except Exception as e:
        logger.error(f"Error plotting data: {e}")
        logger.error(
            f"Check your output files to ensure you only have baseline or optimization files!"
        )


def plotLinks():
    try:
        links = {}
        numHours = 0
        for file in os.listdir("./output/links"):
            numHours += 1
            if file.endswith(".csv"):
                linksCsv = pd.read_csv(f"./output/links/{file}")
                linksCsv = linksCsv.set_index("link").T.to_dict()
                for link in linksCsv.keys():
                    if link not in links:
                        links[link] = 0
                    links[link] += linksCsv[link]["util"]
        for link in links.keys():
            links[link] /= numHours

        sortedLinks = dict(
            sorted(links.items(), key=lambda item: item[1], reverse=True)
        )
        plt.bar(sortedLinks.keys(), sortedLinks.values())
        plt.xlabel("Link")
        plt.ylabel("Average Utilization (%)")
        plt.xticks(rotation=60)
        plt.xticks(range(0, len(sortedLinks.keys()), 300))
        plt.show()
    except Exception as e:
        logger.error(f"Error plotting data: {e}")
