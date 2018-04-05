from sqlalchemy import or_, and_

from rkn.db.dbhandler import DatabaseHandler
from rkn.db.scheme import *


class BlockData(DatabaseHandler):
    """
    Successor class, which provides blocked resources data
    """

    def __init__(self, connstr):
        super(ResourceBlocker, self).__init__(connstr)

    def getBlockedResourcesQuery(self, entitytype):
        """
        :param entitytype: resource entitytype
        :return: query
        """
        return self._session.query(Resource.value). \
            join(Entitytype, Resource.entitytype_id == Entitytype.id). \
            filter(Entitytype.name == entitytype). \
            filter(Resource.is_blocked == True)


    def getBlockedResourcesSet(self, entitytype):
        """
        :param entitytype: resource entitytype
        :return: resources' values set
        """
        try:
            return {'ip': self._getBlockedIPSet}\
                [entitytype]()
        except KeyError:
            return None

    def _getBlockedIPSet(self):
        query = getBlockedResourcesQuery('ip')

        ipSet = {resrow.value for resrow in query.all()}

        return ipSet
