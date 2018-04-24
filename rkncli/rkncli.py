#!/usr/bin/env python3

import sys
import yaml
import argparse

sys.path.append('../')
from rkn import dbutils

CONFIG_PATH = 'config.yml'


CLI_DICT = {
    'resource': {'add': {'args': ['entitytype', 'value'],
                         'func': dbutils.addCustomResource
                         },
                 'del': {'args': ['entitytype', 'value'],
                         'func': dbutils.delCustomResource
                         },
                 'find': {'args': ['value', '...'],
                          'func': dbutils.findResource,
                          'help': 'Point columns or all will be shown'
                          }
                 },
    'content': {'del': {'args': ['outer_id'],
                        'func': None
                        },
                'get': {'args': ['outer_id', '...'],
                        'func': dbutils.getContent,
                        'help': 'Add \'full\' to show resource info'
                        },
                'find': {'args': ['value', '...'],
                         'func': dbutils.findResource
                         }
                }
}


# Parsing arguments
def parseArgs():
    """
    Parses argv, loades config.yml
    :return args
    """
    argparser = argparse.ArgumentParser('RKNDB command line')
    argparser.add_argument('-c', default=CONFIG_PATH, dest='confpath',
                           help='Configuration path')
    argparser.add_argument('--connstr', dest='connstr',
                           help='''engine://user:pswd@host:port/dbname''')

    subparsers = argparser.add_subparsers(title='Commands', dest='subject')
    for subject, actiondict in CLI_DICT.items():
        subjparser = subparsers.add_parser(subject)
        subsubparsers = subjparser.add_subparsers(title='Actions', dest='action')
        for action, actdict in actiondict.items():
            actparser = subsubparsers.add_parser(action, help=actdict.get('help'))
            for arg in actdict['args']:
                if arg == '...':
                    actparser.add_argument('args', nargs='*')
                else:
                    actparser.add_argument(arg)


    if len(sys.argv) == 1:
        argparser.print_help()
        print('\nCommand reference:\n')
        print(yaml.dump(CLI_DICT))
        return None

    return argparser.parse_args()


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
    try:
        return yaml.load(open(configpath))
    except:
        return None

def buildConnStr(engine, host, port, dbname, user, password, **kwargs):
    return engine + '://' + \
           user + ':' + password + '@' + \
           host + ':' + str(port) + '/' + dbname


def main():
    parsedargs = parseArgs()
    if parsedargs is None:
        return 2
    args = vars(parsedargs)
    # If argv are invalid, the program would exit and no actions would be further

    config = initConf(args['confpath'])
    if args['connstr'] is None and config is not None:
        args['connstr'] = buildConnStr(**config['DB'])
    elif args['connstr'] is None and config is None:
        print('Define a connection string!')
        return 3
    try:
        print(str(
            CLI_DICT[args['subject']][args['action']]['func'](**args)
        ))
    except KeyError:
        print('No such key')

if __name__ == "__main__":
    main()
