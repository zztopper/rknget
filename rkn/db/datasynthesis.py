from rkn.db.dbhandler import DatabaseHandler
from rkn.db.scheme import *


class DataSynthesizer(DatabaseHandler):
    """
    Successor class, which provides data synthesis functions
    """

    _orgList = dict()
    _blocktypeList = dict()
    _entitytypeList = dict()

    def __init__(self, connstr):
        super(DataSynthesizer, self).__init__(connstr)
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

    def addResource(self, content_id, entitytype, value, synthetic=True, last_change=None):
        # Let the KeyErrorException raise if an alien blocktype revealed
        entitytype_id = self._entitytypeList[entitytype]

        self._session.add(Resource(content_id=content_id,
                                   last_change=last_change,
                                   entitytype_id=entitytype_id,
                                   value=value,
                                   synthetic=synthetic))
        self._session.flush()

    def purgeResourceSynthetic(self):
        self._session.query(Resource).filter_by(synthetic=True).delete(synchronize_session='evaluate')
        self._session.commit()

