import logging

from rkn.db.resourceblocking import ResourceBlocker


def blockResources(connstr, *args):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :param args: blockings maps
    :return: maybe one day...
    """
    logger = logging.getLogger()

    resblocker = ResourceBlocker(connstr)
    # It may slow down but is safe
    resblocker.unblockAllResources()
    # Fairly blocking first
    logger.debug('Blocking fairly (as is)')
    rows = resblocker.blockFairly()
    logger.info('Blocked fairly ' + str(rows) + ' rows')

    for src, dst in args:
            logger.info('Blocking ' + str(dst) + ' from ' + str(src) + '...')
            rows = resblocker.blockResources(src, dst)
            if rows is not None:
                logger.info('Blocked ' + str(rows) + ' rows')
            else:
                logger.warning('No such entity as ' + str(src) + ' or ' + str(dst))

    resblocker.commitclose()

