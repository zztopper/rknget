#!/usr/bin/env python3

import sys
import yaml
import logging
import os
from http.client import HTTPConnection, HTTPSConnection
import base64
import json
import ssl

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


def _base64httpcreds(user, password):
    # Encoding 'user:password' string to base64 and then to ASCII string back.
    return base64.b64encode((str(user) + ':' + str(password)).encode()).decode('ascii')


def updateF5datagroup(host, port, secure, timeout, datagroup, user, password, urls, **kwargs):
    """
    :param urls: iterable set of URLs, without proto
    PUTs and POSTs json data to the datagroup
    :return: True/False and short result
    """
    # Preparing data to put
    jsondata = json.dumps(
        {'records':
            [
                {'name': url, 'data': ''}
                for url in urls
            ]
        }
    )
    if secure:
        conn = HTTPSConnection(host=host, port=port, timeout=timeout,
                               context=ssl._create_unverified_context())
    else:
        conn = HTTPConnection(host=host, port=port, timeout=timeout)
    headers = {
        'Authorization': 'Basic ' + _base64httpcreds(user, password),
        'Content-Type': 'application/json',
        'Content-Length': len(jsondata)
    }
    try:
        conn.request(method='PUT',
                     url='/mgmt/tm/ltm/data-group/internal/~Common~' + datagroup,
                     body=jsondata,
                     headers=headers)
        resp = conn.getresponse()
    except Exception as e:
        return False, str(e)
    if resp.code != 200:
        return False, 'HTTP response: ' + str(resp.status) + ' - ' + str(resp.reason)
    try:
        return True, 'Generation: ' + str(json.loads(resp.read().decode())['generation'])
    except:
        return True, ''


def saveF5config(host, port, secure, timeout, user, password, **kwargs):
    """
    :param urls: iterable set of URLs, starting with proto or not - no matter
    PUTs and POSTs json data to the datagroup
    :return: True/False
    """
    if secure:
        conn = HTTPSConnection(host=host, port=port, timeout=timeout,
                               context=ssl._create_unverified_context())
    else:
        conn = HTTPConnection(host=host, port=port, timeout=timeout)

    jsondata = '{"command":"save"}'
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': len(jsondata),
        'Authorization': 'Basic ' + _base64httpcreds(user, password)
    }
    try:
        conn.request(method='POST',
                     url='/mgmt/tm/sys/config',
                     body=jsondata,
                     headers=headers)
        resp = conn.getresponse()
    except Exception as e:
        return False, str(e)
    if resp.code != 200:
        return False, 'HTTP response: ' + resp.status + ' ' + resp.reason
    return True



def main():
    configPath = confpath_argv()
    if configPath is None:
        print_help()
        return 0

    config = initConf(configPath)

    logger = initLog(**config['Logging'])
    logger.debug('Successfully started at with config:\n' + str(config))
    createFolders(config['Global']['tmppath'])

    try:
        running = webconn.call(**config['API'],
                               module='api.procutils',
                               method='checkRunning',
                               procname=PROCNAME)
    except Exception as e:
            logger.critical('Couldn\'t obtain information from the database\n' + str(e))
            return 9
    if running and not config['Global'].get('forcerun'):
        logger.critical('The same program is running at this moment. Halting...')
        return 0
    # Getting PID
    log_id = webconn.call(**config['API'],
                          module='api.procutils',
                          method='addLogEntry',
                          procname=PROCNAME)

    try:
        # Fetching http restrictions
        logger.info('Fetching restrictions list from DB')

        urlsSet = {url.lstrip('http://') for url in
                   webconn.call(**config['API'],
                                module='api.restrictions',
                                method='getBlockedHTTP')
                   }
        if config['Extra']['https']:
            urlsSet.update(
                {url.lstrip('https://') for url in
                 webconn.call(**config['API'],
                              module='api.restrictions',
                              method='getBlockedHTTPS')
                 }
            )
        if config['Extra']['domain']:
            urlsSet.update(
                webconn.call(**config['API'],
                             module='api.restrictions',
                             method='_getBlockedDataList',
                             entityname='domain')
            )
        if config['Extra']['domain-mask']:
            urlsSet.update(
                webconn.call(**config['API'],
                             module='api.restrictions',
                             method='_getBlockedDataList',
                             entityname='domain-mask')
            )
        if config['Extra']['ip']:
            urlsSet.update(
                webconn.call(**config['API'],
                             module='api.restrictions',
                             method='_getBlockedDataList',
                             entityname='ip')
            )
        if config['Extra']['ipsubnet']:
            urlsSet.update(
                webconn.call(**config['API'],
                             module='api.restrictions',
                             method='getBlockedIPsFromSubnets')
            )
        # Truncating entries if too many.
        if len(urlsSet) > config['Extra']['truncate-after']:
            logger.debug('Truncating entries: ' + str(len(urlsSet) - config['Extra']['truncate-after']))
            urlsSet = list(urlsSet)[-config['Extra']['truncate-after']:]

        logger.info('Entries being blocked: ' + str(len(urlsSet)))
        logger.info('Updating F5 configuration...')
        result = ['URLs to restrict: ' + str(len(urlsSet))]

        for host in config['F5']:
            logger.info('Host: ' + host['host'])
            saved = False
            # Putting URLs to F5
            success, strcode = updateF5datagroup(urls=urlsSet, **host)
            if success:
                # Then saving
                saved = saveF5config(**host)
                if saved:
                    logger.info('Configuration is up to date and saved')
                else:
                    logger.warning('Not saved, it\'s strange...')
            else:
                logger.warning('Couldn\'t update')
            res = 'F5 ' + host['host'] + ' status: ' + \
                  ['ERROR ', 'OK '][success] + strcode + \
                  [' not ', ' '][saved] + 'saved'

            logger.debug(res)
            result.append(res)

        # Updating the state in the database
        webconn.call(**config['API'],
                     module='api.procutils',
                     method='finishJob',
                     log_id=log_id,
                     exit_code=0,
                     result='\n'.join(result))
        logger.info('Blocking was finished, enjoy your 1984th')

    except Exception as e:
        webconn.call(**config['API'],
                     module='api.procutils',
                     method='finishJob',
                     log_id=log_id,
                     exit_code=1,
                     result=str(e))
        logger.error(str(e))
        return getattr(e, 'errno', 1)

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
