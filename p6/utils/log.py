import os
import sys
import logging
import datetime

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

def setupCustomLogger(name):
    outdir = config.get('DEFAULT', 'logging-dir')
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_filename = f"{outdir}/p6_{timestamp}.log"
    logging.basicConfig(filename=log_filename, level=_logLevel(config.get('DEFAULT', 'logging-level')), format=format)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    
    return logger

def _logLevel(level):
    if level == 'DEBUG':
        return logging.DEBUG
    elif level == 'INFO':
        return logging.INFO
    elif level == 'WARNING':
        return logging.WARNING
    elif level == 'ERROR':
        return logging.ERROR
    elif level == 'CRITICAL':
        return logging.CRITICAL
    else:
        return logging.INFO