from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from rkn.db.scheme import *


class DatabaseHandler:

    _engine = None
    _sessionmaker = None
    _session = None
    _now = None

    _orgList = dict()
    _blocktypeList = dict()
    _entitytypeList = dict()

    def __init__(self, connstr):
        self._engine = create_engine(connstr, echo=False)
        self._sessionmaker = sessionmaker(bind=self._engine)
        self._session = self._sessionmaker()
        self._InitTableDicts()
        self._now = datetime.now()

    def commitclose(self):
        self._session.commit()
        self._session.close()

    def _getNameIDMapping(self, table):
        """
        :param: table
        :return: dict NAME -> ID
        """
        dbim = dict()
        for row in self._session.query(table):
            dbim[row.name] = row.id
        return dbim


    def _InitTableDicts(self):
        """
        Fetching dictionaries for future usage
        """
        self._blocktypeList = self._getNameIDMapping(BlockType)
        self._entitytypeList = self._getNameIDMapping(Entitytype)
        self._orgList = self._getNameIDMapping(Organisation)

    def addDecision(self, date, number, org):
        """
        :param date
        The arguments were named corresponding with
        <content> tag attributes to simplify kwargs passthrough
        """


        # Adding missing organisation to the table
        if self._orgList.get(org) is None:
            newOrg = Organisation(name=org)
            self._session.add(newOrg)
            self._session.commit()
            self._orgList[org] = newOrg.id

        # Insert or update is not supported by this ORM module

        des_id = self._session.query(Decision.id).filter_by(decision_code=number).first()
        if des_id is not None:
            return des_id

        newDes = Decision(decision_date=date,
                 decision_code=number,
                 org_id=self._orgList[org])

        self._session.add(newDes)
        self._session.flush()
        return newDes.id

    def _addProcInfo(self, content_id):
        self._session.add(ProcInfo(content_id=content_id, add_time=self._now, del_time=None))

    def addContent(self, decision_id, id, includeTime,
                   hash, entryType, blocktype='default', ts=None, **kwargs):
        # Let the KeyErrorException raise if an alien blocktype revealed
        blocktype_id = self._blocktypeList[blocktype]

        # Checking whether content is in the table but disabled
        cnt = self._session.query(Content).filter_by(outer_id=id).first()
        if cnt is not None and not cnt.in_dump:
            # Cascade purging must place to be
            self._session.delete(cnt)
            self._session.flush()

        newContent = Content(
            outer_id=id,
            include_time=includeTime,
            hash=hash,
            last_change=ts,
            in_dump=True,
            decision_id=decision_id,
            blocktype_id=blocktype_id,
            entrytype_id=entryType
        )
        self._session.add(newContent)
        self._session.flush()
        self._addProcInfo(newContent.id)
        return newContent.id

    def getOuterIDSet(self):
        return {cnt.outer_id for cnt in self._session.query(Content.outer_id).filter_by(in_dump=True).all()}

    def disableRemovedContent(self, outerinset):
        self._session.query(Content).filter_by(Content.outer_id.in_(outerinset)).update({'in_dump': False})
        self._session.query(ProcInfo).filter_by(ProcInfo.outer_id.in_(outerinset)).update({'del_date': self._now})
        self._session.flush()

    def addResource(self, content_id, entitytype, value, synthetic=True, last_change=None):
        # Let the KeyErrorException raise if an alien blocktype revealed
        entitytype_id = self._entitytypeList[entitytype]

        self._session.add(Resource(content_id=content_id,
                                   last_change=last_change,
                                   entitytype_id=entitytype_id,
                                   value=value,
                                   synthetic=synthetic))
        self._session.flush()

