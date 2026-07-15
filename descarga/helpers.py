import json
import datetime
import logging
import time

def writeJson(filepath, dictionary):
   
    with open(filepath, 'w') as fp:
        json.dump(dictionary, fp)

def readJson(filepath):
  
    with open(filepath, 'r') as fp:
        data = json.load(fp)
    return data

def getRemotePath(rootPath, product, datetimeIn):

    year = str(datetimeIn.year)
    day_of_year = datetimeIn.strftime('%j')
    hour = datetimeIn.strftime('%H')

    outPath = rootPath + product + '/' + year + '/' + day_of_year + '/' + hour + '/'

    return outPath, year, day_of_year, hour

def createLogger(attachedFile, logPath):
   
    logger = logging.getLogger(attachedFile)
    logger.setLevel(logging.DEBUG)
    log_name = datetime.date.today().strftime('%Y%m%d_%H%M%S') + '_logfile.log'
    logfile_name = logPath + log_name
    logfile = logging.FileHandler(logfile_name)
    logfile.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logfile.setFormatter(formatter)
    logger.addHandler(logfile)

    return logger, logfile
