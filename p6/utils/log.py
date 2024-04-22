import sys
import logging
import datetime

def setupCustomLogger(name):
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_filename = f"p6_{timestamp}.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO, format=format)


    logger = logging.getLogger(name)
    logger.addHandler(handler)
    
    return logger