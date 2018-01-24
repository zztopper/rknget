#!/usr/bin/env python3

import yaml
import logging
import os
from rkn import rknstatehandler, rknsoapwrapper, rkndumpparse


# Importing configuration
config = yaml.load(open('config.yml'))


# Initialising logger, returns logger
def initLog(logpath='log.log', stdoutlvl='DEBUG', logfilelvl='INFO', **kwargs):
    logger = logging.getLogger()
    logger.setLevel(logging.getLevelName(logfilelvl))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler = logging.FileHandler(logpath)
    filehandler.setLevel(logging.getLevelName(logfilelvl))
    filehandler.setFormatter(formatter)
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.getLevelName(stdoutlvl))
    streamhandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    logger.addHandler(streamhandler)

    logger.debug('Successfully started with config:\n' + str(config))

    return logger


def createFolders(*args):
    """
    Creates nesessary folders
    :param args: paths tuple
    :return: Nothing
    """
    for path in args:
        try:
            os.makedirs(path, mode=0o755, exist_ok=True)
        finally:
            pass


def saveData(outpath, datamapping, outdata):
    """
    Saves parsed datasets to files defined.
    :param outpath: tuple of paths
    :param datamapping: dict datatype -> filename
    :param outdata: data dict datatype -> set
    :return: None
    """

    datafiledesc = {fname: [
        open(file=path+'/'+fname, mode='w', buffering=1)
        for path in outpath
    ]
        for fname in set(datamapping.values())
    }
    for datakey in outdata:
        for file in datafiledesc[datamapping[datakey]]:
            file.write('\n'.join(outdata[datakey]) + '\n')

def main():
    logger = initLog(**config['Logging'])

    createFolders(config['Global']['tmppath'], *config['Global']['outpath'])

    # Loading state values from file
    if not os.path.exists(config['Global']['statepath']):
        logger.warning('State file is absent, but don\'t worry')

    lastRknState = rknstatehandler.RknStateHandler(config['Global']['statepath'])

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

    if lastRknState.isActual():
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

    try:
        outdata = rkndumpparse.parse(dumpFile)
    except Exception as e:
        logger.error(e)
        lastRknState.updateParseInfo(None)
        return 3
    logger.info('Blocklist was parsed successfully')

    saveData(config['Global']['outpath'], config['DataMapping'], outdata)
    logger.info('Parsed data was saved')

    # save debug data to the state file
    datasetsizes = {dtype: len(outdata[dtype])
                    for dtype in outdata.keys()}
    datasetsizes['urlsCount'] = sum(datasetsizes.values())

    lastRknState.updateParseInfo(datasetsizes)
    return 0


if __name__ == "__main__":
    main()
