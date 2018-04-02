#!/usr/bin/env python3

import sys
import yaml
import logging
import os
from rkn import rknstatehandler, rknsoapwrapper, dumpparse, synthetic

CONFIG_PATH = 'config.yml'


# Importing configuration
def initConf():
    """
    Parses argv, loades config.yml
    :return: Configusration tree
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
    logger.setLevel(logging.getLevelName(stdoutlvl))
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
    :return: Nothingzzzя
    """
    for path in args:
        try:
            os.makedirs(path, mode=0o755, exist_ok=True)
        finally:
            pass


def buildConnStr(engine, host, port, dbname, user, password, **kwargs):
    return engine + '://' + \
           user + ':' + password + '@' + \
           host + ':' + str(port) + '/' + dbname


def main():
    config = initConf()
    if config is None:
        print('Usage: ')
        return 0

    logger = initLog(**config['Logging'])
    logger.debug('Successfully started at with config:\n' + str(config))
    createFolders(config['Global']['tmppath'])

    # Loading state values from file
    if not os.path.exists(config['Global']['statepath']):
        logger.warning('State file is absent, but don\'t worry')
    lastRknState = rknstatehandler.RknStateHandler(config['Global']['statepath'])

    Obtaining dump file
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
        logger.info('Last dump is relevant')
        return 0
    logger.info('Blocklist is outdated, requesting a new dump')
    try:
        dumpFile = rknSW.getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
                                     open(config['Global']['reqPathSig'], 'rb').read()
                                     )
    except Exception as e:
        logger.error(e)
        return 2

    if config['Global']['savetmp']:
        open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='wb').write(dumpFile)
    # If you do wanna use downloaded file, take this instead of 'Loading' block above
    # dumpFile = open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='rb').read()

    connstr = buildConnStr(**config['DB'])
    # Parsing dump file
    try:
        # TODO: return something debugging
        nodata = dumpparse.parse(dumpFile, connstr)
        # Freeing memory
        del dumpFile
        #if config['Miscellaneous']['Synthetic']:
        #    synthetic.something(connstr)
    except Exception as e:
        logger.error(e)
        lastRknState.updateParseInfo(None)
        return 3

    logger.info('Blocklist has been parsed successfully')
    # Saving Success to the state file
    lastRknState.updateParseInfo({"Success": True})
    return 0


if __name__ == "__main__":
    main()
