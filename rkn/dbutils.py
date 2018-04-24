from rkn.db.dbops import DBOperator
from rkn import parseutils

"""
This module provides API for 'rkncli' utility.
Every function should return a string or many.
"""
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
            DBOperator(connstr).addCustomResource(
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
    :return: True if deleted, False otherwise
    """
    try:
        return(
            DBOperator(connstr).delCustomResource(
                entitytype=entitytype,
                value=value,
            )
        )
    except KeyError:
        return "Entity type error"


def findResource(connstr, value, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """
    if kwargs.get('args') is None:
        kwargs['args'] = []
    headers, rows = DBOperator(connstr).findResource(value, *kwargs['args'])
    result = list()
    result.append('\t'.join(headers))
    for row in rows:
        result.append('\t'.join(map(str, row)))

    return '\n'.join(result)


def getContent(connstr, outer_id, **kwargs):

    headers, row = DBOperator(connstr).getContent(outer_id)
    result = list()
    result.append('\t'.join(headers))
    result.append('\t'.join(map(str, row)))
    if 'full' in kwargs.get('args'):
        content_id = row[headers.index('id')]
        headers, rows = DBOperator(connstr).getResourceByContentID(content_id)
        result.append('RESOURCES')
        result.append('\t'.join(headers))
        for row in rows:
            result.append('\t'.join(map(str, row)))

    return '\n'.join(result)