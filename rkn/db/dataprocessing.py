from sqlalchemy import or_, and_

from rkn.db.dbhandler import DatabaseHandler
from rkn.db.scheme import *


class DataProcessor(DatabaseHandler):
    """
    Successor class, which provides data processing functions
    """

    _orgList = dict()
    _blocktypeList = dict()
    _entitytypeList = dict()

    def __init__(self, connstr):
        super(DataProcessor, self).__init__(connstr)
        self._initTableDicts()

    def _getNameIDMapping(self, table):
        """
        :param: table
        :return: dict NAME -> ID
        """
        dbim = dict()
        for row in self._session.query(table):
            dbim[row.name] = row.id
        return dbim

    def _initTableDicts(self):
        """
        Fetching dictionaries for future usage
        """
        self._blocktypeList = self._getNameIDMapping(BlockType)
        self._entitytypeList = self._getNameIDMapping(Entitytype)
        self._orgList = self._getNameIDMapping(Organisation)

    def addDumpInfoRecord(self, updateTime, updateTimeUrgently, **kwargs):
        """
        The arguments were named corresponding with
        <reg> tag attributes to simplify kwargs passthrough
        """
        dump_info_record = DumpInfo(update_time=updateTime,
                                    update_time_urgently=updateTimeUrgently,
                                    parse_time=self._now,
                                    parsed=False)
        self._session.add(dump_info_record)
        self._session.commit()
        return dump_info_record.id

    def setDumpParsed(self, dump_id):
        dump_info_record = self._session.query(DumpInfo).filter_by(id=dump_id).first()
        dump_info_record.parsed = True
        self._session.commit()

    def addDecision(self, date, number, org):
        """
        The arguments were named corresponding with
        <decision> tag attributes to simplify kwargs passthrough
        """
        # Adding missing organisation to the table
        if self._orgList.get(org) is None:
            newOrg = Organisation(name=org)
            self._session.add(newOrg)
            # Let it be committed, not so much orgs exist
            self._session.flush()
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

    def addContent(self, dump_id, decision_id, id, includeTime,
                   hash, entryType, blockType='default', ts=None, **kwargs):
        """
        The arguments were named corresponding with
        <content> tag attributes to simplify kwargs passthrough
        """
        # Let the KeyErrorException raise if an alien blocktype revealed
        blocktype_id = self._blocktypeList[blockType]

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
            entrytype_id=entryType,
            first_dump_id=dump_id,
            last_dump_id=dump_id
        )
        self._session.add(newContent)
        self._session.flush()
        return newContent.id

    def getOuterIDSet(self):
        # The set is faster because unsorted
        return {cnt.outer_id for cnt in self._session.query(Content.outer_id).filter_by(in_dump=True).all()}

    def updateContentPresence(self, dump_id, disabledIDSet):
        # The list is required to avoid *args passthrough
        # filter_by shouldn't be used with in_ and notin_
        if len(disabledIDSet) > 0:
            self._session.query(Content).filter(Content.outer_id.in_(disabledIDSet))\
                .update({'in_dump': False}, synchronize_session=False)
        self._session.query(Content).filter(Content.in_dump == True)\
            .update({'last_dump_id': dump_id}, synchronize_session=False)
        self._session.flush()

    def addResource(self, content_id, entitytype, value, synthetic=False, last_change=None):
        # Let the KeyErrorException raise if an alien blocktype revealed
        entitytype_id = self._entitytypeList[entitytype]

        self._session.add(Resource(content_id=content_id,
                                   last_change=last_change,
                                   entitytype_id=entitytype_id,
                                   value=value,
                                   synthetic=synthetic))
        self._session.flush()

