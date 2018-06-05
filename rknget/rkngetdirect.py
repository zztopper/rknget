#!/usr/bin/env python3

"""
This version of rknget was saved for low memory usecases.
Instead of POSTing dump.xml to the web app server via API,
it works directly with the database using API modules.
"""

import sys
import yaml
import logging
import os
import io
import zipfile

sys.path.append('../')
sys.path.append('../rkn')
from api import dumpparse, blocking, procutils
from dbconn import connstr
import rknsoapwrapper
from common import utils

CONFIG_PATH = 'config.yml'

PROCNAME = __file__.split(os.path.sep)[-1].split('.')[0]


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
        running = procutils.checkRunning(connstr, PROCNAME)
    except Exception as e:
        logger.critical('Couldn\'t obtain information from the database\n' + str(e))
        return 9
    if running and not config['Global'].get('forcerun'):
        logger.critical('The same program is running at this moment. Halting...')
        return 0
    log_id = procutils.addLogEntry(connstr, PROCNAME)

    try:
        if config['Miscellaneous']['uselocaldump']:
            dumpFile = open(file=config['Global']['dumpPath'],
                            mode='rb').read()
        else:
            # Checking dump info
            logger.debug('Obtaining dumpfile from ' + config['DumpLoader']['url'])
            rknSW = rknsoapwrapper.RknSOAPWrapper(**config['DumpLoader'])
            dumpDate = rknSW.getLastDumpDateEx()
            if not dumpDate:
                raise Exception('Couldn\'t obtain dumpdates info', errno=2)
            update_time = max(dumpDate['lastDumpDate'],
                              dumpDate['lastDumpDateUrgently'])/1000

            parsed_recently =  dumpparse.parsedRecently(update_time,connstr)

            if parsed_recently:
                result = 'Last dump is relevant'
                logger.info(result)
                # Updating the state in database
                procutils.finishJob(connstr, log_id, 0, result)
                return 0

            # Obtaining dump file
            logger.info('Blocklist is outdated, requesting a new dump')
            dumpFile = rknSW.getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
                                         open(config['Global']['reqPathSig'], 'rb').read()
                                         )
            if config['Global']['savedump']:
                open(file=config['Global']['dumpPath'], mode='wb').write(dumpFile)

        # Parsing dump file
        xmldump = zipfile.ZipFile(io.BytesIO(dumpFile)).read('dump.xml').decode('cp1251')
        # Freeing memory
        del dumpFile

        dumpparse.parse(xmldump, connstr)
        # Freeing memory
        del xmldump
        logger.info('Dump have been parsed to database successfully')

        # Blocking
        rowsdict = dict()
        # It may slow down but is safe
        blocking.unblockResources(connstr)
        # Fairly blocking first
        logger.debug('Blocking fairly (as is)')
        rows = blocking.blockResourcesFairly(connstr)
        rowsdict['fairly'] = rows
        logger.info('Blocked fairly ' + str(rows) + ' rows')
        for src, dst in config['Blocking']:
            logger.info('Blocking ' + str(dst) + ' from ' + str(src))
            rows = blocking.blockResourcesExcessively(connstr, src, dst)
            if rows is not None:
                logger.info('Blocked ' + str(rows) + ' rows')
                rowsdict[str(dst) + '->' + str(src)] = rows
            else:
                logger.warning('Nothing have been blocked from' + str(src) + ' to ' + str(dst))
        # Blocking custom resouces
        if config['Miscellaneous']['custom']:
            logger.info('Blocking custom resources')
            rows = blocking.blockCustom(connstr)
            logger.info('Blocked ' + str(rows))
            rowsdict['Custom'] = rows

        # Unblocking
        whitelist = config['Miscellaneous']['whitelist']
        if whitelist is not None:
            logger.info('Unblocking whitelist')
            rows = blocking.unblockSet(connstr, whitelist)
            logger.info('Unblocked ' + str(rows))
            rowsdict['Undone'] = rows

        # Updating the state in the database
        result = 'Blocking results\n' + '\n'.join(k + ':' + str(v) for k,v in rowsdict.items())
        procutils.finishJob(connstr, log_id, 0, result)
        logger.info('Blocking was finished, enjoy your 1984th')

    except Exception as e:
        procutils.finishJob(connstr, log_id, 1, str(e))
        logger.error(str(e))
        return getattr(e, 'errno', 1)

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
