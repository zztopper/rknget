#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import subprocess

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


def getUnboundLocalDomains(binarypath, stubip, **kwargs):
    """
    Gets domains set from unbound local zones data
    :param binarypath: path to unbound-control
    :param stubip: ip used for stub
    :return: domains set
    """
    proc = subprocess.Popen(args=[binarypath, 'list_local_data'],
                            encoding='UTF8',
                            stdout=subprocess.PIPE)
    # Filtered RKN domains
    domains = set()
    for stdoutrow in proc.communicate()[0].split('\n'):
        rowdata = stdoutrow.split('\t')
        if len(rowdata) == 5 and rowdata[4] == stubip:
            domains.add(rowdata[0][:-1])
    #
    proc = subprocess.Popen(args=[binarypath, 'list_local_zones'],
                            encoding='UTF8',
                            stdout=subprocess.PIPE)

    wdomains = set()
    for stdoutrow in proc.communicate()[0].split('\n'):
        rowdata = stdoutrow.split(' ')
        if len(rowdata) == 2 and rowdata[1] == 'redirect':
            try:
                domains.remove(rowdata[0][:-1])
            except KeyError:
                continue
            wdomains.add(rowdata[0][:-1])


    return domains, wdomains


def addUnboundZones(binarypath, stubip, domainset, zonetype, **kwargs):
    """
    Adds domains stubs via unbound-control
    :param binarypath: path to unbound-control
    :param domainset: domains set
    :param zonetype: 'static', 'redirect', 'transparent', etc. See unbound.conf manuals.
    :return: blocked domains count
    """
    # for domain in domainset:
    #     subprocess.call([binarypath, 'local_zone', domain, zonetype], stdout=devnull)
    #     subprocess.call([binarypath, 'local_data', domain + '. IN A ' + stubip], stdout=devnull)
    devnull = open(os.devnull, "w")
    stdin = (' ' + zonetype + '\n').join(domainset) + ' ' + zonetype + '\n'
    s = subprocess.Popen([binarypath, 'local_zones'],
                         stdout=devnull,
                         stdin=subprocess.PIPE,
                         encoding='UTF8')
    s.communicate(input=stdin)
    stdin = ('. IN A ' + stubip + '\n').join(domainset) + '. IN A ' + stubip + '\n'
    s = subprocess.Popen([binarypath, 'local_datas'],
                         stdout=devnull,
                         stdin=subprocess.PIPE,
                         encoding='UTF8')
    s.communicate(input=stdin)
    return len(domainset)


def delUnboundZones(binarypath, domainset, **kwargs):
    """
    Deletes domains stubs via unbound-control
    :param binarypath: path to unbound-control
    :param domainset: domains set
    :return: blocked domains count
    """
    devnull = open(os.devnull, "w")
    stdin = '\n'.join(domainset) + '\n'
    s = subprocess.Popen([binarypath, 'local_zones_remove'],
                         stdout=devnull,
                         stdin=subprocess.PIPE,
                         encoding='UTF8')
    s.communicate(input=stdin)

    return len(domainset)


def buildUnboundConfig(confpath, stubip, domainset, wdomainset, **kwargs):
    configfile = open(file=confpath, mode='w')

    for domain in domainset:
        configfile.write('local-zone: "' + domain + '" transparent\n')
        configfile.write('local-data: "' + domain + '. IN A 10.1.1.3"\n\n')

    for wdomain in wdomainset:
        configfile.write('local-zone: "' + wdomain + '" redirect\n')
        configfile.write('local-data: "' + wdomain + '. IN A 10.1.1.3"\n\n')

    configfile.close()


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
        logger.info('Obtaining current domain blocklists on unbound daemon')
        domainUBCSet, wdomainUBCSet = getUnboundLocalDomains(**config['Unbound'])

        logger.info('Fetching restrictions list from DB')
        domainBlockSet, wdomainBlockSet = restrictions.getBlockedDomainsMerged(connstr)

        logger.info('Banning...')
        addDcount = addUnboundZones(**config['Unbound'],
                                    domainset=domainBlockSet - domainUBCSet,
                                    zonetype='static')
        addWDcount = addUnboundZones(**config['Unbound'],
                                     domainset=wdomainBlockSet - wdomainUBCSet,
                                     zonetype='redirect')
        logger.info('Unbanning...')
        delDcount = delUnboundZones(**config['Unbound'],
                                    domainset=domainUBCSet - domainBlockSet)
        delWDcount = delUnboundZones(**config['Unbound'],
                                     domainset=wdomainUBCSet - wdomainBlockSet)

        logger.info('Generating permanent config...')
        buildUnboundConfig(**config['Unbound'],
                           domainset=domainBlockSet,
                           wdomainset=wdomainBlockSet
                           )
        result = ['Unbound updates:',
                  'added: ' + str(addDcount),
                  'added_wildcard: ' + str(addWDcount),
                  'deleted: ' + str(delDcount),
                  'deleted_wildcard: ' + str(delWDcount)
                  ]
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
