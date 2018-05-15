#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import io
import zipfile

import rknsoapwrapper
sys.path.append('../')
from rkn import webconn

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
    logger.setLevel(logging.DEBUG)
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


def main():
    configPath = confpath_argv()
    if configPath is None:
        print_help()
        return 0

    config = initConf(configPath)

    logger = initLog(**config['Logging'])
    logger.debug('Starting with config:\n' + str(config))

    createFolders(config['Global']['tmpPath'])

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
            parsed_recently = webconn.call(module='api.dumpparse',
                                           method='parsedRecently',
                                           update_time=update_time,
                                           **config['API'])

            if parsed_recently:
                result = 'Last dump is relevant'
                logger.info(result)
                # Updating the state in database
                webconn.call(module='api.procutils',
                             method='finishJob',
                             log_id=log_id,
                             exit_code=0,
                             result=result,
                             **config['API'])
                return 0

            # Obtaining dump file
            logger.info('Blocklist is outdated, requesting a new dump')
            dumpFile = rknSW.getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
                                         open(config['Global']['reqPathSig'], 'rb').read()
                                         )
            if config['Global']['savedump']:
                open(file=config['Global']['dumpPath'], mode='wb').write(dumpFile)

        # Parsing dump file
        logger.info('Parsing dump file...')
        xmldump = zipfile.ZipFile(io.BytesIO(dumpFile)).read('dump.xml').decode('cp1251')
        # Freeing memory
        del dumpFile

        parse_result = webconn.call(module='api.dumpparse',
                                    method='parse',
                                    xmldump=xmldump,
                                    **config['API'])
        if not parse_result:
            raise Exception('Dump hasn\'t been parsed', errno=3)
        # Freeing memory
        del xmldump
        logger.info('Dump have been parsed to database successfully')

        # Blocking
        rowsdict = dict()
        # It may slow down but is safe
        webconn.call(module='api.blocking',
                     method='unblockResources',
                     **config['API'])
        # Fairly blocking first
        logger.debug('Blocking fairly (as is)')
        rows = webconn.call(module='api.blocking',
                            method='blockResourcesFairly',
                            **config['API'])
        rowsdict['fairly'] = rows
        logger.info('Blocked fairly ' + str(rows) + ' rows')
        for src, dst in config['Blocking']:
            logger.info('Blocking ' + str(dst) + ' from ' + str(src))
            rows = webconn.call(module='api.blocking',
                                method='blockResourcesExcessively',
                                src_entity=src,
                                dst_entity=dst,
                                **config['API'])
            if rows is not None:
                logger.info('Blocked ' + str(rows) + ' rows')
                rowsdict[str(dst) + '->' + str(src)] = rows
            else:
                logger.warning('Nothing have been blocked from' + str(src) + ' to ' + str(dst))
        # Blocking custom resouces
        if config['Miscellaneous']['custom']:
            logger.info('Blocking custom resources')
            rows = webconn.call(module='api.blocking',
                                method='blockCustom',
                                **config['API'])
            logger.info('Blocked ' + str(rows))
            rowsdict['Custom'] = rows

        # Updating the state in the database
        result = 'Blocking results\n' + '\n'.join(k + ':' + str(v) for k,v in rowsdict.items())
        # Updating the state in database
        webconn.call(module='api.procutils',
                     method='finishJob',
                     log_id=log_id,
                     exit_code=0,
                     result=result,
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
