from rkn.db.dataprocessing import DataProcessor
from rkn import parseutils

from datetime import datetime
import ipaddress


def addCustomResource(connstr, entitytype, value, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """
    try:
        return(
            DataProcessor(connstr).addResource(
                content_id=None,
                entitytype=entitytype,
                value=value,
                is_custom=True,
                last_change=datetime.now().astimezone()
            )
        )
    except KeyError:
        return None


def findResource(connstr, value, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """

    return 'test'
