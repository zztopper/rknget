#!/usr/bin/env python3

import sys
import argparse
import yaml

sys.path.append('../')
from rkn import webconn

CONFIG_PATH = 'config.yml'

CLI_MOD = 'api.dbutils'

CLI_DICT = {
    'dumpinfo': {'show': {'args': [],
                          'func': 'showDumpInfo',
                          },
                 'stats': {'args': [],
                           'func': 'showDumpStats',
                           }
                 },
    'resource': {'add': {'args': ['entitytype', 'value'],
                         'func': 'addCustomResource'
                         },
                 'del': {'args': ['entitytype', 'value'],
                         'func': 'delCustomResource'
                         },
                 'find': {'args': ['entitytype', 'value', '...'],
                          'func': 'findResource',
                          'help': 'Point columns, else all will be shown. ' +
                                  'Set \'all\' for any entitytype'
                          }
                 },
    'content': {'del': {'args': ['outer_id'],
                        'func': 'delContent'
                        },
                'get': {'args': ['outer_id', '...'],
                        'func': 'getContent',
                        'help': 'Add \'full\' to show resource info'
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


def main():
    parsedargs = parseArgs()
    if parsedargs is None:
        return 2
    args = vars(parsedargs)
    # If argv are invalid, the program would exit and no actions would be further

    config = initConf(args['confpath'])
    try:
        print(str(
            webconn.call(module=CLI_MOD,
                         method=CLI_DICT[args['subject']][args['action']]['func'],
                         **config['API'],
                         **args)
        ))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
