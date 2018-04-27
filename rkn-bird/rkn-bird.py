#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import subprocess
from datetime import datetime

sys.path.append('../')
from rkn import restrictions, procutils

CONFIG_PATH = 'config.yml'

PROCNAME = __file__.split(os.path.sep)[-1].split('.')[0]


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
    :return: Nothing
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


def updateStateYML(statepath, **kwargs):
    """
    Considered to merge dicts
    :param statepath: the path to a file
    :param kwargs: any state parameters you want
    """
    try:
        state = yaml.load(open(file=statepath, mode='r'))
        yaml.dump({**state, **kwargs},
                  open(file=statepath, mode='w'),
                  default_flow_style=False)
    except:
        yaml.dump(kwargs,
                  open(file=statepath, mode='w'),
                  default_flow_style=False)


def updateBirdConfig(confpath, stubip, ipsubset, restartcmd, **kwargs):
    configfile = open(file=confpath, mode='w')
    for ipsub in ipsubset:
        configfile.write('route ' + ipsub + ' via ' + stubip + ';\n')
    configfile.close()
    subprocess.call(restartcmd.split(' '), shell=True)


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

    try:
        running = procutils.checkRunning(connstr, PROCNAME)
    except Exception as e:
        logger.critical('Couldn\'t obtain information from the database\n' + str(e))
        return 9
    if running and not config['Global'].get('forcerun'):
        logger.critical('The same program is running at this moment. Halting...')
        return 0
    log_id = procutils.addLogEntry(connstr, PROCNAME)

    try:
        # Fetching ip restrictions
        logger.info('Fetching restrictions list from DB')
        totalblocked, ipsubSet = restrictions.getBlockedIPsMerged(connstr)
        logger.info('Updating bird configuration and restarting daemon...')
        # Updating BGP casts
        updateBirdConfig(**config['Bird'],
                         ipsubset=ipsubSet)
        # Updating the state in the database
        result = [str(totalblocked) + ' ip entries are routed to blackhole',
                  str(len(ipsubSet)) + ' entries are announced by BGP daemon']
        logger.info(', '.join(result))
        procutils.finishJob(connstr, log_id, 0, '\n'.join(result))
        logger.info('Blocking was finished, enjoy your 1984th')

    except Exception as e:
        procutils.finishJob(connstr, log_id, 1, str(e))
        logger.error(str(e))
        return getattr(e, 'errno', 1)

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
