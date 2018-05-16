from sqlalchemy import or_, and_
from sqlalchemy import func
from sqlalchemy.orm import aliased

from db.dataprocessing import DataProcessor
from db.scheme import *


class DBOperator(DataProcessor):
    """
    Successor class, which provides operations for CLI API (dbutils)
    """

    _resourceQuery = None
    _contentQuery = None

    def __init__(self, connstr):
        super(DBOperator, self).__init__(connstr)
        self._resourceQuery = self._session.query(Resource.id,
                                                  Content.outer_id,
                                                  Entitytype.name,
                                                  BlockType.name,
                                                  Resource.is_custom,
                                                  Resource.is_blocked,
                                                  Resource.value). \
            outerjoin(Content, Resource.content_id == Content.id). \
            join(Entitytype, Resource.entitytype_id == Entitytype.id). \
            outerjoin(BlockType, Content.blocktype_id == BlockType.id)
        DumpInfoA = aliased(DumpInfo, name='DumpInfoA')
        self._contentQuery = self._session.query(Content.id,
                                                 Content.outer_id,
                                                 Content.include_time,
                                                 Content.in_dump,
                                                 Resource.is_blocked,
                                                 DumpInfo.parse_time.label('first_time'),
                                                 DumpInfoA.parse_time.label('last_time')). \
            join(BlockType, Content.blocktype_id == BlockType.id). \
            join(DumpInfo, Content.first_dump_id == DumpInfo.id). \
            join(DumpInfoA, Content.last_dump_id == DumpInfoA.id)

    def addCustomResource(self, entitytype, value):
        """
        Adds custom resource to the table.
        :return: new or existing resource ID
        """
        # Let the KeyErrorException raise if an alien blocktype revealed
        entitytype_id = self._entitytypeDict[entitytype]

        # Checking if such resource exists
        res = self._session.query(Resource).\
            filter_by(entitytype_id=entitytype_id).\
            filter_by(value=value). \
            filter_by(is_custom=True). \
            first()

        if res is None:
            return self.addResource(content_id=None,
                                    last_change=self._now,
                                    entitytype=entitytype,
                                    value=value,
                                    is_custom=True)
        else:
            return res.id

    def delCustomResource(self, entitytype, value):
        """
        Deletes custom resource from the table.
        :return: True if deleted, False otherwise
        """
        # Let the KeyErrorException raise if an alien blocktype revealed
        entitytype_id = self._entitytypeDict[entitytype]

        result = self._session.query(Resource). \
            filter_by(entitytype_id=entitytype_id). \
            filter_by(value=value). \
            filter_by(is_custom=True). \
            delete()

        return [False, True][result]

    def findResource(self, value, entitytype=None, *args):
        """
        Searches resources in the table by value
        :param value: value to search in
        :param fields: column names
        :param entitytype: type of entity or any if not set
        :return: All entries matching the value. With headers.
        """
        if value == '':
            query = self._resourceQuery
        else:
            query = self._resourceQuery. \
                filter(Resource.value.like('%' + value + '%'))

        entitytype_id = self._entitytypeDict.get(entitytype)
        if entitytype_id is not None:
            query = query.filter(Resource.entitytype_id == entitytype_id)

        rows = query.all()
        return self._outputQueryRows(rows, *args)

    def getContent(self, outer_id):
        row = self._contentQuery. \
            filter(Content.outer_id == outer_id).first()
        if row:
            return row._fields, list(row)
        else:
            return [], []

    def getResourceByContentID(self, content_id, *args):
        rows = self._resourceQuery. \
            filter(Resource.content_id == content_id).all()
        return self._outputQueryRows(rows, *args)

    def getBlockCounters(self):
        rows = self._session.query(Entitytype.name,
                                   func.count(True)). \
            join(Resource, Resource.entitytype_id == Entitytype.id). \
            group_by(Entitytype.id).all()
        return self._outputQueryRows(rows)

    def delContent(self, outer_id):
        """
        Deletes content from the table.
        :return: True if deleted, False otherwise
        """
        result = self._session.query(Content). \
            filter_by(outer_id=outer_id). \
            delete()

        return [False, True][result]

    def getLastDumpInfo(self):
        """
        The same function as the dataprocessing's one.
        Returns the last dump state. If no entries, empty dict.
        :return: dict column->value or dict().
        """
        row = self._session.query(DumpInfo). \
            order_by(DumpInfo.id.desc()).first()
        fields = DumpInfo.__table__.columns.keys()
        if row is None:
            return dict()
        return {
            f: getattr(row, f) for f in fields
        }

    def unlockJobs(self, procname=None):
        query = self._session.query(Log). \
            filter(Log.exit_code is None)
        if procname is not None:
            query = query.filter(Log.procname == procname)

        result = query.update({'exit_code': 255, 'result': 'Supressed'},
                              synchronize_session=False)
        return result

    def getActiveJobs(self, procname=None):
        query = self._session.query(Log.id,
                                    Log.start_time,
                                    Log.procname). \
            filter(Log.exit_code is None)
        if procname is not None:
            query = query.filter(Log.procname == procname)
        rows = query.order_by(DumpInfo.id.desc()).all()

        return self._outputQueryRows(rows)
