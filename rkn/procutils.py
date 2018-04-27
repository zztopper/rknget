from rkn.db.procdata import ProcData

"""
This module works with Log
"""


def checkRunning(connstr, procname):
    """
    Checks if this instance has already been started not so far
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: True if the same program is running, else False
    """
    return ProcData(connstr).checkRunning(procname)

def addLogEntry(connstr, procname):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: Log id for this process instance
    """
    return ProcData(connstr).addLogEntry(procname)


def finishJob(connstr, log_id, exit_code, result):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: Log id for this process instance
    """
    return ProcData(connstr).finishJob(log_id, exit_code, result)

