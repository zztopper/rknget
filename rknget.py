#!/usr/bin/env python3

import sys
import yaml
import logging
import os
from rkn import rknstatehandler, rknsoapwrapper, rkndumpparse


CONFIG_PATH = 'config.yml'


# Importing configuration
def initConf():
    """
    Parses argv, loades config.yml
    :return: Configuration tree
    """
    # Yeah, I'm too laze to use argparse
    if len(sys.argv) == 1:
        return yaml.load(open(CONFIG_PATH))

    if len(sys.argv) == 3 and sys.argv[2] == '-c':
        return yaml.load(open(sys.argv[3]))

    print('Usage: ' + sys.argv[0] + ' (with ./config.yml)\n' +
          'Usage: ' + sys.argv[0] + ' -c [CONFIG PATH]')
    exit(0)


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


def saveData(datamapping, outdata):
    """
    Saves parsed datasets to files defined.
    :param outpath: tuple of paths
    :param datamapping: dict datatype -> filename
    :param outdata: data dict datatype -> set
    :return: None
    """

    # Cleansing files if any exists
    for dfiles in datamapping.values():
        for file in dfiles:
            open(file, 'w').close()

    for dtype in outdata.keys():
        # You might not save some data
        if datamapping.get(dtype) is None:
            continue
        # Or you might of course
        for file in datamapping[dtype]:
            f = open(file=file, mode='a+t', buffering=1)
            f.write('\n'.join(outdata[dtype]) + '\n')
            f.close()


def main():
    config = initConf()
    if config is None:
        print('Usage: ')
        return 0

    logger = initLog(**config['Logging'])

    logger.debug('Successfully started with config:\n' + str(config))

    createFolders(config['Global']['tmppath'])

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
    logger.info('Blocklist has been parsed successfully')

    # Freeing memory
    del dumpFile

    saveData(config['DataMapping'], outdata)

    if config['Global']['savetmp']:
        tmpDataMapping = {dtype: [config['Global']['tmppath'] + '/' + dtype]
                          for dtype in rkndumpparse.datatypes}
        saveData(tmpDataMapping, outdata)
        pass

    logger.info('Parsed data have been saved')

    # save debug data to the state file
    datasetsizes = {dtype: len(outdata[dtype])
                    for dtype in outdata.keys()}
    datasetsizes['urlsCount'] = sum(datasetsizes.values())

    lastRknState.updateParseInfo(datasetsizes)
    return 0


if __name__ == "__main__":
    main()
