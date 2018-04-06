#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import subprocess

from rkn import restrictions

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


def saveState(dom_dum, statepath):
    """
    Simple writer
    :param statepath: the path to a file
    :param dom_dum: blocked domains count, 0 after failure
    """
    open(statepath, 'w').write(str(dom_dum))


def getUnboundLocalDomainsSet(binarypath, stubip, **kwargs):
    """
    Gets domains set from unbound local zones data
    :param binarypath: path to unbound-control
    :param stubip: ip used for stub
    :return: domains set
    """
    proc = subprocess.Popen(args=[binarypath, 'list_local_data'],
                            stdout=subprocess.PIPE)
    # Filtered RKN domains
    domains = set()
    for stdoutrow in proc.communicate()[0].split('\n'):
        rowdata = stdoutrow.split('\t')
        if rowdata[4] == stubip:
            domains.add(rowdata[0][:-1])
    #
    proc = subprocess.Popen(args=[binarypath, 'list_local_zones'],
                            stdout=subprocess.PIPE)

    wdomains = set()
    for stdoutrow in proc.communicate()[0].split('\n'):
        rowdata = stdoutrow.split(' ')
        if rowdata[1] == 'redirect':
            wdomains.add(rowdata[0][:-1])
            domains.remove(rowdata[0][:-1])

    return domains, wdomains


def main():
    configPath = confpath_argv()
    if configPath is None:
        print_help()
        return 0

    config = initConf(configPath)

    logger = initLog(**config['Logging'])
    logger.debug('Successfully started at with config:\n' + str(config))
    createFolders(config['Global']['tmppath'])

    connstr = buildConnStr(**config['DB'])
    # Parsing dump file
    try:
        domainBlockSet, wdomainBlockSet = restrictions.getBlockedDomainsCleared(connstr)
    except Exception as e:
        logger.error(e)
        saveState(0, config['Global']['statepath'])
        return 1

    domainUBCSet, wdomainUBCSet = getUnboundLocalDomainsSet(**config['Unbound'])



    # TODO: unbound-control, savefile
    #domainSet
    #config['Global']['savetmp']:

    # TODO: sum dom + dommask? distinct?
    saveState(len(domainSet), config['Global']['statepath'])

    logger.info('Blocking was finished, enjoy your 1984')
    return 0


if __name__ == "__main__":
    main()
