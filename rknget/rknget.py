#!/usr/bin/env python3

import sys
import yaml
import logging
import os

sys.path.append('../')
from rkn import rknstatehandler, rknsoapwrapper, dumpparse, synthetic, blocking

CONFIG_PATH = 'config.yml'


# Parsing arguments
def confpath_argv():
    """
    Parses argv, loades config.yml
    :return: config path
    """
    if len(sys.argv) == 1:
        return CONFIG_PATH

    if len(sys.argv) == 3 and sys.argv[2] == '-c':
        return sys.argv[3]

    return None


# Print help
def print_help():
    print('Usage: ' + sys.argv[0] + ' (with ./config.yml)\n' +
          'Usage: ' + sys.argv[0] + ' -c [CONFIG PATH]')


# Importing configuration
def initConf(configpath):
    """
    Loades YAML config
    :return: Configuration tree
    """
    return yaml.load(open(configpath))


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
    configPath = confpath_argv()
    if configPath is None:
        print_help()
        return 0

    config = initConf(configPath)

    logger = initLog(**config['Logging'])
    logger.debug('Successfully started at with config:\n' + str(config))
    createFolders(config['Global']['tmppath'])

    # Loading state values from file
    if not os.path.exists(config['Global']['statepath']):
        logger.warning('State file is absent, but don\'t worry')
    lastRknState = rknstatehandler.RknStateHandler(config['Global']['statepath'])

    # Obtaining dump file
    # logger.debug('Obtaining dumpfile from ' + config['DumpLoader']['url'])
    # try:
    #     rknSW = rknsoapwrapper.RknSOAPWrapper(**config['DumpLoader'])
    # except Exception as e:
    #     logger.error('Couldn\'t connect to RKN WSDL\n' + str(e))
    #
    # dumpDate = rknSW.getLastDumpDateEx()
    # if not dumpDate:
    #     logger.error('Couldn\'t obtain dumpdates info')
    #     return 1
    # lastRknState.updateTimeStamps(dumpDate['lastDumpDate'],
    #                               dumpDate['lastDumpDateUrgently'])
    #
    # if lastRknState.isActual():
    #     logger.info('Last dump is relevant')
    #     return 0
    # logger.info('Blocklist is outdated, requesting a new dump')
    # try:
    #     dumpFile = rknSW.getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
    #                                  open(config['Global']['reqPathSig'], 'rb').read()
    #                                  )
    # except Exception as e:
    #     logger.error(e)
    #     return 2
    #
    # if config['Global']['savetmp']:
    #     open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='wb').write(dumpFile)

    # If you do wanna use downloaded file, take this instead of 'Loading' block above
    dumpFile = open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='rb').read()

    connstr = buildConnStr(**config['DB'])
    # Parsing dump file
    try:
        # TODO: return something debugging
        nodata = dumpparse.parse(dumpFile, connstr)
        # Freeing memory
        del dumpFile
    except Exception as e:
        logger.error(e)
        lastRknState.updateParseInfo(None)
        return 3

    logger.info('Dump have been parsed to database successfully')

    # Synthetic
    # Not implemented yet
    if config['Miscellaneous']['Synthetic']:
        synthetic.updateSynthetic(connstr)
        logger.info('Synthetic restrictions have been generated')
    else:
        synthetic.purgeSynthetic(connstr)
        logger.info('There are no synthetic restrictions from now')

    # Blocking
    blocking.blockResources(connstr, *config['Blocking'])
    # Saving Success to the state file
    lastRknState.updateParseInfo({"Success": True})
    logger.info('Blocking was finished, enjoy your 1984th')
    return 0


if __name__ == "__main__":
    main()
