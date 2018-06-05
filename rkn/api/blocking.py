from db.resourceblocking import ResourceBlocker


def unblockResources(connstr):
    resblocker = ResourceBlocker(connstr)
    resblocker.unblockAllResources()


def blockResourcesFairly(connstr):
    """
    Enables blocking resoures according to its blocktype and presence in the dump
    Any other blocking is excessive a priori
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: blocked rows count
    """
    return ResourceBlocker(connstr).blockFairly()


def blockResourcesExcessively(connstr, src_entity, dst_entity):
    """
    Blocks dst_entities from src_entities data.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: blocked rows count
    """
    return ResourceBlocker(connstr).blockExcessively(src_entity, dst_entity)


def blockCustom(connstr):
    """
    Blocks custom resources.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: blocked rows count
    """
    return ResourceBlocker(connstr).blockCustom()


def unblockSet(connstr, resSet):
    """
    Unblocking set of resources.
    It may cause violations and bad consequences!
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :param resSet: the set of resources
    :return: blocked rows count
    """
    return ResourceBlocker(connstr).unblockSet(resSet)
