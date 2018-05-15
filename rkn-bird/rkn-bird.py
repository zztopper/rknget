#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import subprocess
import shutil

sys.path.append('../')
from common import webconn, utils

PROCNAME = __file__.split(os.path.sep)[-1].split('.')[0]


# def updateStateYML(statepath, **kwargs):
#     """
#     Considered to merge dicts
#     :param statepath: the path to a file
#     :param kwargs: any state parameters you want
#     """
#     try:
#         state = yaml.load(open(file=statepath, mode='r'))
#         yaml.dump({**state, **kwargs},
#                   open(file=statepath, mode='w'),
#                   default_flow_style=False)
#     except:
#         yaml.dump(kwargs,
#                   open(file=statepath, mode='w'),
#                   default_flow_style=False)


def updateBirdConfig(confpath, stubip, ipsublist, restartcmd, **kwargs):
    configfile = open(file=confpath, mode='w')
    for ipsub in ipsublist:
        configfile.write('route ' + ipsub + ' via ' + stubip + ';\n')
    configfile.close()
    subprocess.call([restartcmd], shell=True)


def main():
    configPath = utils.confpath_argv()
    if configPath is None:
        utils.print_help()
        return 0

    config = utils.initConf(configPath)

    logger = utils.initLog(**config['Logging'])
    logger.debug('Starting with config:\n' + str(config))

    utils.createFolders(config['Global']['tmppath'])

    try:
        running = webconn.call(module='api.procutils',
                               method='checkRunning',
                               procname=PROCNAME,
                               **config['API'])
    except Exception as e:
            logger.critical('Couldn\'t obtain information from the database\n' + str(e))
            return 9
    if running and not config['Global'].get('forcerun'):
        logger.critical('The same program is running at this moment. Halting...')
        return 0
    # Getting PID
    log_id = webconn.call(module='api.procutils',
                          method='addLogEntry',
                          procname=PROCNAME,
                          **config['API'])

    try:
        # Fetching ip restrictions
        logger.info('Fetching restrictions list from DB')
        ipsublist, totalblocked = webconn.call(module='api.restrictions',
                                               method='getBlockedIPsMerged',
                                               **config['API'])
        logger.info('Updating bird configuration and restarting daemon...')
        # Updating BGP casts
        updateBirdConfig(ipsublist=ipsublist,
                         **config['Bird'])
        if config['Global']['saveconf']:
            shutil.copy(config['Bird']['confpath'],
                        config['Global']['tmppath'])

        # Updating the state in the database
        result = [str(totalblocked) + ' ip entries are routed to blackhole',
                  str(len(ipsublist)) + ' entries are announced by BGP daemon']
        logger.info(', '.join(result))
        # Updating the state in the database
        webconn.call(module='api.procutils',
                     method='finishJob',
                     log_id=log_id,
                     exit_code=0,
                     result='\n'.join(result),
                     **config['API'])
        logger.info('Blocking was finished, enjoy your 1984th')

    except Exception as e:
        webconn.call(module='api.procutils',
                     method='finishJob',
                     log_id=log_id,
                     exit_code=1,
                     result=str(e),
                     **config['API'])
        logger.error(str(e))
        return getattr(e, 'errno', 1)

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
