#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil

sys.path.append('../')
from common import webconn, utils

PROCNAME = __file__.split(os.path.sep)[-1].split('.')[0]


def getUnboundLocalDomains(binarypath, stubip, **kwargs):
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
    for stdoutrow in proc.communicate()[0].decode().split('\n'):
        rowdata = stdoutrow.split('\t')
        if len(rowdata) == 5 and rowdata[4] == stubip:
            domains.add(rowdata[0][:-1])
    #
    proc = subprocess.Popen(args=[binarypath, 'list_local_zones'],
                            stdout=subprocess.PIPE)

    wdomains = set()
    for stdoutrow in proc.communicate()[0].decode().split('\n'):
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
    # One-by-one adding
    # for domain in domainset:
    #     subprocess.call([binarypath, 'local_zone', domain, zonetype], stdout=devnull)
    #     subprocess.call([binarypath, 'local_data', domain + '. IN A ' + stubip], stdout=devnull)
    if len(domainset) == 0:
        return
    devnull = open(os.devnull, "w")
    stdin = (' ' + zonetype + '\n').join(domainset) + ' ' + zonetype + '\n'
    s = subprocess.Popen([binarypath, 'local_zones'],
                         stdout=devnull,
                         stdin=subprocess.PIPE)
    s.communicate(input=stdin.encode())
    stdin = ('. IN A ' + stubip + '\n').join(domainset) + '. IN A ' + stubip + '\n'
    s = subprocess.Popen([binarypath, 'local_datas'],
                         stdout=devnull,
                         stdin=subprocess.PIPE)
    s.communicate(input=stdin.encode())


def delUnboundZones(binarypath, domainset, **kwargs):
    """
    Deletes domains stubs via unbound-control
    :param binarypath: path to unbound-control
    :param domainset: domains set
    :return: blocked domains count
    """
    if len(domainset) == 0:
        return
    devnull = open(os.devnull, "w")
    stdin = '\n'.join(domainset) + '\n'
    s = subprocess.Popen([binarypath, 'local_zones_remove'],
                         stdout=devnull,
                         stdin=subprocess.PIPE)
    s.communicate(input=stdin.encode())


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
        logger.info('Obtaining current domain blocklists on unbound daemon')
        domainUBCSet, wdomainUBCSet = getUnboundLocalDomains(**config['Unbound'])

        logger.info('Fetching restrictions list from DB')
        domainBlockSet, \
        wdomainBlockSet = webconn.call(module='api.restrictions',
                                       method='getBlockedDomains',
                                       collapse=config['Unbound']['collapse'],
                                       **config['API'])
        logger.info('Obtained ' + str(len(domainBlockSet)) + ' strict domains and ' +
                    str(len(wdomainBlockSet)) + ' wildcard domains')
        # Lists were got, transforming
        domainBlockSet = set(domainBlockSet)
        wdomainBlockSet = set(wdomainBlockSet)

        logger.info('Banning...')
        result = ['Unbound updates:']

        domainset = domainBlockSet - domainUBCSet
        addUnboundZones(domainset=domainset,
                        zonetype='static',
                        **config['Unbound'])
        logger.debug('Strict banned: ' + ' '.join(map(str, domainset)))
        result.append('Strict banned: ' + str(len(domainset)))

        domainset = wdomainBlockSet - wdomainUBCSet
        addUnboundZones(domainset=domainset,
                        zonetype='redirect',
                        **config['Unbound'])
        logger.debug('Wildcard banned: ' + ' '.join(map(str, domainset)))
        result.append('Wildcard banned: ' + str(len(domainset)))

        logger.info('Unbanning...')

        domainset = domainUBCSet - domainBlockSet
        delUnboundZones(domainset=domainset,
                        zonetype='static',
                        **config['Unbound'])
        logger.debug('Strict unbanned: ' + ' '.join(map(str, domainset)))
        result.append('Strict unbanned: ' + str(len(domainset)))

        domainset = wdomainUBCSet - wdomainBlockSet
        delUnboundZones(domainset=domainset,
                        zonetype='redirect',
                        **config['Unbound'])
        logger.debug('Wildcard unbanned: ' + ' '.join(map(str, domainset)))
        result.append('Wildcard unbanned: ' + str(len(domainset)))

        logger.info('Generating permanent config...')
        buildUnboundConfig(domainset=domainBlockSet,
                           wdomainset=wdomainBlockSet,
                           **config['Unbound']
                           )
        if config['Global']['saveconf']:
            shutil.copy(config['Unbound']['confpath'],
                        config['Global']['tmppath'])

        logger.info(', '.join(result))
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
