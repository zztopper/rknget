from rkn.db.dataprocessing import DataProcessor
from rkn import parseutils

# Checks
checks = {
    'ip': parseutils._isip,
    'ipsubnet': parseutils._isipsub,
    'domain': parseutils.isdomain,
    'domain-mask': parseutils.isdomain
}


def addCustomResource(connstr, entitytype, value, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """
    try:
        if not checks[entitytype](value):
            return 'Value error'
    except KeyError:
        # No checks for this entity type, but going ahead.
        pass
    try:
        return(
            DataProcessor(connstr).addCustomResource(
                entitytype=entitytype,
                value=value,
            )
        )
    except KeyError:
        return "Entity type error"


def delCustomResource(connstr, entitytype, value, **kwargs):
    """
    Deletes custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None if nothing have been done
    """

    return 'test'


def findResource(connstr, value, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """

    return 'test'
