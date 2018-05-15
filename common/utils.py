"""
Common functions and patterns for the most of RKN scripts
"""
import logging
import sys
import yaml
import os


def initLog(logpath='log.log', stdoutlvl='DEBUG', logfilelvl='INFO', **kwargs):
    """
    Initialize two loggers: stdout and file
    :return: logger instance
    """

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


