import os
import sys
import logging

from datetime import datetime
from dotenv import load_dotenv

load_dotenv("variables.env")


def setupCustomLogger(name):
    outdir = os.getenv("LOGGING_DIR")
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = f"{outdir}/{timestamp}_p6.log"
    logging.basicConfig(
        filename=log_filename,
        level=_logLevel(os.getenv("LOGGING_LEVEL")),
        format=format,
    )

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    return logger


def _logLevel(level):
    match level:
        case "DEBUG":
            return logging.DEBUG
        case "INFO":
            return logging.INFO
        case "WARNING":
            return logging.WARNING
        case "ERROR":
            return logging.ERROR
        case "CRITICAL":
            return logging.CRITICAL
        case _:
            return logging.INFO
