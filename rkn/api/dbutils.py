from db.dbops import DBOperator
from api import parseutils

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


def _dbAsText(headers, rows):
    """
    Auxilliary function.
    :param headers: headers list
    :param rows: list of values lists
    :return:
    """
    result = list()
    result.append('\t'.join(headers))
    for row in rows:
        result.append('\t'.join(map(str, row)))
    return '\n'.join(result)


def testConn(connstr, **kwargs):
    """
    Tests a connection.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return:
    """
    try:
        DBOperator(connstr)
        return 'OK'
    except Exception as e:
        return str(e)


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


def findResource(connstr, value, entitytype=None, **kwargs):
    """
    Adds custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: row ID or None for erroneous entitytype
    """
    if kwargs.get('args') is None:
        kwargs['args'] = []
    if entitytype == 'all':
        entitytype = None
    return _dbAsText(*DBOperator(connstr).findResource(value, entitytype, *kwargs['args']))


def getContent(connstr, outer_id, **kwargs):

    headers, row = DBOperator(connstr).getContent(outer_id)
    result = _dbAsText(headers, [row])
    if kwargs.get('args') is not None \
            and 'full' in kwargs.get('args'):
        content_id = row[headers.index('id')]
        result = result + '\nRESOURCES\n'
        result = result + _dbAsText(*DBOperator(connstr).getResourceByContentID(content_id))

    return result


def showDumpStats(connstr, **kwargs):

    return _dbAsText(*DBOperator(connstr).getBlockCounters())


def showDumpInfo(connstr, **kwargs):

    return '\n'.join(str(k).ljust(16) + '\t' + str(v)
                     for k, v in DBOperator(connstr).getLastDumpInfo().items())


def delContent(connstr, outer_id, **kwargs):
    """
    Deletes custom resource to the database's Resource table.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: True if deleted, False otherwise
    """
    return DBOperator(connstr).delContent(outer_id)


def unlockJobs(connstr, procname=None, **kwargs):
    """
    Sets exit_code and result of the all log entires with empty exit_code.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :param procname: specify procname to unlock
    :return: Affected entries count.
    """
    if procname == 'all':
        procname = None

    return DBOperator(connstr).unlockJobs(procname)


def getActiveJobs(connstr, procname=None, **kwargs):

    if procname == 'all':
        procname = None
    return _dbAsText(*DBOperator(connstr).getActiveJobs(procname))


def getLastJobs(connstr, procname=None, **kwargs):

    if kwargs.get('args') is None:
        count = 10
    elif len(kwargs['args']) == 0:
        count = 10
    else:
        count = kwargs['args'][0]

    if procname == 'all':
        procname = None

    return _dbAsText(*DBOperator(connstr).getLastJobs(procname, count))

