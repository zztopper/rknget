from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class DatabaseHandler:
    """
    Base abstract class
    """

    _now = None
    _engine = None
    _sessionmaker = None
    _session = None

    def __init__(self, connstr):
        self._now = datetime.now().astimezone()
        self._engine = create_engine(connstr, echo=False)
        self._sessionmaker = sessionmaker(bind=self._engine)
        self._session = self._sessionmaker()

    def __del__(self):
        self.commitclose()
        del self._now
        del self._session
        del self._sessionmaker
        del self._engine

    def commitclose(self):
        self._session.commit()
        self._session.close()

    def _outputQueryRows(self, rowslist, *fields):
        """
        Common function.
        :param rowslist: The list of rows returned by select query.
        :param fields: arbitrary list of existing fields
        :return: fields list and values list's list
        """
        if len(rowslist) == 0:
            return [], [[]]
        if len(fields) == 0:
            return list(rowslist[0]._fields), [list(row) for row in rowslist]
        else:
            return fields, [[getattr(row, f) for f in fields] for row in rowslist]
