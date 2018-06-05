from sqlalchemy import or_, and_

from db.dbhandler import DatabaseHandler
from db.scheme import *


class ResourceBlocker(DatabaseHandler):
    """
    Successor class, which provides resource blocking functions
    """

    _entitytypeDict = dict()

    def __init__(self, connstr):
        super(ResourceBlocker, self).__init__(connstr)
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
        self._entitytypeDict = self._getNameIDMapping(Entitytype)


    def unblockAllResources(self):
        self._session.query(Resource).update({'is_blocked': False}, synchronize_session=False)

    def blockExcessively(self, src_entity, dst_entity):
        """
        Blocks dst_entities from src_entities data.
        :return: Blocked rows count if implemented, else None
        """
        try:
            src_entity_id = self._entitytypeDict[src_entity]
            dst_entity_id = self._entitytypeDict[dst_entity]
        except KeyError:
            return None
        return self._blockRelated(src_entity_id, dst_entity_id)

    def _blockResourcesByIDs(self, idSet):
        """
        Blocking resources by ID
        :param idSet: iterable
        """
        self._session.query(Resource).filter(Resource.id.in_(idSet)) \
            .update({'is_blocked': True}, synchronize_session=False)

    def blockFairly(self):
        """
        Enables blocking resoures according to its blocktype and presence in the dump
        Any other blocking is excessive a priori
        """
        # Understand as you consider
        res_id_data = self._session.query(Resource.id). \
            join(Content, Resource.content_id == Content.id). \
            join(BlockType, Content.blocktype_id == BlockType.id). \
            join(Entitytype, Resource.entitytype_id == Entitytype.id). \
            filter(
                or_(
                    and_(BlockType.name == 'default',
                         or_(Entitytype.name == 'http', Entitytype.name == 'https')),
                    and_(BlockType.name == 'domain', Entitytype.name == 'domain'),
                    and_(BlockType.name == 'domain-mask', Entitytype.name == 'domain-mask'),
                    and_(BlockType.name == 'ip',
                         or_(Entitytype.name == 'ip', Entitytype.name == 'ipsubnet')),
                )
            ). \
            filter(Content.in_dump == True)
        ids = {resrow.id for resrow in res_id_data.all()}
        self._blockResourcesByIDs(ids)
        return len(ids)

    def _blockRelated(self, src_entity_id, dst_entity_id):
        """
        Generic function without resource.value handlers
        Blocks entities related with a content entry.
        :param src_entity: usually it's an entity which has already been blocked according to its blocktype
        :param dst_entity: an antity for blocking
        :return: blocked rows count
        """
        # Understand as you consider
        cnt_id_data = self._session.query(Resource.content_id). \
            join(Content, Resource.content_id == Content.id). \
            filter(Resource.entitytype_id == src_entity_id). \
            filter(Content.in_dump == True)

        cnt_ids = {cnt_id_data.content_id for cnt_id_data in cnt_id_data.all()}

        res_id_data = self._session.query(Resource.id). \
            join(Entitytype, Resource.entitytype_id == Entitytype.id). \
            filter(Resource.content_id.in_(cnt_ids)). \
            filter(Resource.entitytype_id == dst_entity_id)

        ids = {resrow.id for resrow in res_id_data.all()}

        self._blockResourcesByIDs(ids)
        return len(ids)

    def blockCustom(self):
        """
        Enables blocking custom resources
        :return: blocked rows count
        """
        rows_count_affected = self._session.query(Resource).filter_by(is_custom=True) \
            .update({'is_blocked': True}, synchronize_session=False)
        return rows_count_affected

    def unblockSet(self, resSet):
        """
        Unblocking set of resources.
        :return: blocked rows count
        """
        if len(resSet) == 0:
            return 0
        res_query = self._session.query(Resource)
        res_filter = list()
        for res in resSet:
            res_filter.append(Resource.value.like('%' + res + '%'))
        rows_count_affected = res_query.filter(or_(*res_filter)). \
            update({'is_blocked': False}, synchronize_session=False)
        return rows_count_affected

