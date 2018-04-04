import io
import urllib.parse
import re
import logging

import rkn.util

from rkn.db.dataproc import DatabaseHandler

"""
This module contains custom dataminers from existing info having been already parsed.
"""

def _addDomainsFromHTTPS(dbhandler):
    """
    :param dbhandler: DB Handler class object
    :return:
    """
    resSet = dbhandler.getResourcesSet()

def purgeSynthetic(connstr):
    DatabaseHandler(connstr).purgeResourceSynthetic()

def updateSynthetic(connstr, methods):
    """
    Generates synthetic restrictions from existing resources info.
    :param connstr: connstr: smth like "engine://user:pswd@host:port/dbname"
    :param methods: a set of functions in this module
    :return: none yet
    """
    # Becomes unnecessary
    return True
    # logger = logging.getLogger()
    # for f in methods:
    #     try:
    #         ("_"+str(f))(DatabaseHandler(connstr))
    #     except NotImplementedError e:
    #         logger.warning('Not implemented synthesis: ' + str(f))

