from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseHandler:
    """
    Base abstract class
    """

    _engine = None
    _sessionmaker = None
    _session = None

    def __init__(self, connstr):
        self._engine = create_engine(connstr, echo=False)
        self._sessionmaker = sessionmaker(bind=self._engine)
        self._session = self._sessionmaker()

    def commitclose(self):
        self._session.commit()
        self._session.close()
