import configobj
import logging

from abr_site_parser import app
if __name__ == "__main__":
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    fileHandler = logging.FileHandler("{0}/{1}.log".format('./log', 'debuglog'))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    app.run()
