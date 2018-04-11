#!/usr/bin/env python3

import sys
import yaml
import logging
import os
import subprocess
import datetime

sys.path.append('../')
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
    except TypeError:
        yaml.dump(kwargs,
                  open(file=statepath, mode='w'),
                  default_flow_style=False)


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

    for domain in domainset:
        subprocess.call([binarypath, 'local_zone', domain, zonetype])
        subprocess.call([binarypath, 'local_data', domain + '. IN A ' + stubip])
    return len(domainset)


def delUnboundZones(binarypath, domainset, **kwargs):
    """
    Deletes domains stubs via unbound-control
    :param binarypath: path to unbound-control
    :param domainset: domains set
    :return: blocked domains count
    """

    for domain in domainset:
        subprocess.call([binarypath, 'local_zone_remove', domain])
    return len(domainset)


def genUnboundConfig(confpath, stubip, domainset, wdomainset, **kwargs):
    configfile = open(file=confpath, mode='w')

    for domain in domainset:
        configfile.write('local-zone: "' + domain + '" static\n')
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

    # Creating PID file
    # if os.path.isfile(config['Global']['pidpath']):
    #     logger.warning('The program is suspected to be running ' +
    #                  'as long as the PID file ' + config['Global']['pidfile'] + ' exists.')
    #     logger.info('Delete the PID file manually or wait until the first copy get finished')
    #     return 0
    # else:
    #     open(config['Global']['pidpath'], 'w').close()

    logger.debug('Successfully started at with config:\n' + str(config))
    createFolders(config['Global']['tmppath'])
    updateStateYML(statepath=config['Global']['statepath'],
                   **{'Program': {'start_time': str(datetime.datetime.utcnow())}})

    logger.info('Obtaining current domain blocklists on unbound daemon')
    domainUBCSet, wdomainUBCSet = getUnboundLocalDomains(**config['Unbound'])

    connstr = buildConnStr(**config['DB'])
    # Parsing dump file
    logger.info('Fetching restrictions list from DB')
    try:
        domainBlockSet, wdomainBlockSet = restrictions.getBlockedDomainsCleared(connstr)
        updateStateYML(statepath=config['Global']['statepath'],
                       **{'DB':
                            {'domains': len(domainBlockSet),
                             'wdomains': len(wdomainBlockSet),
                             'last_successfull': True
                             }
                        })
    except Exception as e:
        logger.error(e)
        updateStateYML(statepath=config['Global']['statepath'],
                       **{'DB': {'last_successfull': False}})
        return 1

    try:
        logger.info('Banning...')
        addDcount = addUnboundZones(**config['Unbound'],
                        domainset=domainBlockSet.difference(domainUBCSet),
                        zonetype='static')
        addWDcount = addUnboundZones(**config['Unbound'],
                        domainset=wdomainBlockSet.difference(wdomainUBCSet),
                        zonetype='redirect')
        logger.info('Unbanning...')
        delDcount = delUnboundZones(**config['Unbound'],
                        domainset=domainUBCSet.difference(domainBlockSet))
        delWDcount = delUnboundZones(**config['Unbound'],
                        domainset=wdomainUBCSet.difference(wdomainBlockSet))
        updateStateYML(statepath=config['Global']['statepath'],
                       **{'Unbound':
                              {'added': addDcount,
                               'added_wildcard': addWDcount,
                               'deleted': delDcount,
                               'deleted_wildcard': delWDcount,
                               'last_successfull': True
                               }
                          })
    except Exception as e:
        logger.critical('Something was going wrong, the violations may occur!')
        logger.error(e)
        updateStateYML(statepath=config['Global']['statepath'],
                       **{'DB': {'last_successfull': False}})
        return 2

    logger.info('Generating permanent config...')
    genUnboundConfig(**config['Unbound'],
                     domainset=domainBlockSet,
                     wdomainset=wdomainBlockSet
                     )

    logger.info('Blocking was finished, enjoy your 1984th')
    updateStateYML(statepath=config['Global']['statepath'],
                   **{'Program': {'finish_time': str(datetime.datetime.utcnow())}})
    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
