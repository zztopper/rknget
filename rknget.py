#!/usr/bin/env python3

import yaml
import logging
import os
from lib import rknupdatestate, rknsoapwrapper, rkndumpparser

config = yaml.load(open('config.yml'))


# Initialising logger, returns logger
def initLog(logpath):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler = logging.FileHandler(logpath)
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.DEBUG)
    streamhandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    logger.addHandler(streamhandler)

    logger.debug('Successfully started with config:\n' + str(config))

    return logger

# Importing configuration

def createFolders(**kwargs):
    try:
        os.makedirs(outpath, mode=0o700, exist_ok=True)
        os.makedirs(tmppath, mode=0o700, exist_ok=True)
    finally:
        return 0

def main():
    logger = initLog(config['Global']['logpath'])

    createFolders(**config['Global'])

    # Loading state values from file
    lastRknState = rknupdatestate.RknUpdateState(config['Global']['statepath'])
    # No config found
    if lastRknState.checkTime == 0:
        logger.warning('OK, let\'s start a clean life')

    logger.debug('Obtaining dumpfile from ' + config['DumpLoader']['url'])
    try:
        rknSW = rknsoapwrapper.RknSOAPWrapper(**config['DumpLoader'])

    except Exception as e:
        logger.error('Couldn\'t connect to RKN WSDL\n' + str(e))

    dumpDate = rknSW.getLastDumpDateEx()
    if not dumpDate:
        logger.error('Couldn\'t obtain dumpdates info')
        return 1

    lastRknState.updateTimeStamps(dumpDate['lastDumpDate'],
                                  dumpDate['lastDumpDateUrgently'])

    if lastRknState.downlTime > lastRknState.dumpTime and \
            lastRknState.downlTime > lastRknState.dumpTimeU:
        logger.info('Last dump is actual')
        return 0

    logger.info('Blocklist is outdated')

    try:
        dumpFile = rknSW.getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
                                     open(config['Global']['reqPathSig'], 'rb').read()
                                     )
    except Exception as e:
        logger.error(e)
        return 2

    if config['Global']['savetmp']:
        open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='wb').write(dumpFile)

    # Transforming outdata filenames to paths
    for key in config['DataMapping']:
        config['DataMapping'][key] = config['Global']['outpath'] + '/' + config['DataMapping'][key]

    dumpParser = rkndumpparser.RknDumpParser(dumpFile, config['DataMapping'])
    try:
        urlsCount = dumpParser.parse()
    except Exception as e:
        logger.error(e)
        return 3
    logger.info('Blocklist was parsed successfully')

    lastRknState.updateInfoOnParse(urlsCount)
    return 0


if __name__ == "__main__":
    main()
