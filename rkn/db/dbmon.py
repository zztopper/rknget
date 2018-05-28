from db.dataprocessing import DataProcessor
from db.scheme import *


class DBMonitor(DataProcessor):
    """
    Successor class, which provides operations for CLI API (dbutils)
    """

    _resourceQuery = None
    _contentQuery = None

    def __init__(self, connstr):
        super(DBMonitor, self).__init__(connstr)

    def getLastExitCode(self, procname):
        query = self._session.query(Log.exit_code).\
            filter(Log.procname == procname). \
            order_by(Log.id.desc()).\
            limit(1)
        row = query.first()
        if row is None:
            return None
        return row.exit_code

