from sqlalchemy import or_, and_

from rkn.db.dbhandler import DatabaseHandler
from rkn.db.scheme import *
from datetime import datetime


class ProcData(DatabaseHandler):
    """
    Successor class, which provides blocked resources data
    """

    def __init__(self, connstr):
        super(ProcData, self).__init__(connstr)

    def checkRunning(self, procname):

        row = self._session.query(Log). \
            filter_by(procname=procname). \
            filter_by(exit_code=None).first()
        return row is not None

    def addLogEntry(self, procname):

        row = Log(start_time=self._now,
                  procname=procname)
        self._session.add(row)
        self._session.commit()
        return row.id

    def finishJob(self, log_id, exit_code, result=None):
        row = self._session.query(Log).filter_by(id=log_id).first()
        row.exit_code = exit_code
        row.finish_time = datetime.now().astimezone()
        row.result = result
        self._session.commit()
        return row.id


