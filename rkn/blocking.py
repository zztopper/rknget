import logging

from rkn.db.resourceblocking import ResourceBlocker


def blockResources(connstr, **kwargs):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :param kwargs: blocking modes
    :return: maybe one day...
    """
    logger = logging.getLogger()

    resblocker = ResourceBlocker(connstr)
    # It may slow down but is safe
    resblocker.unblockAllResources()

    for mode, enabled in kwargs.items():
        if enabled:
            logger.debug('Blocking mode processing: ' + str(mode))
            rows = resblocker.blockResources(str(mode))
            if rows is not None:
                logger.info('Blocked ' + str(rows) + ' rows with ' + str(mode) + ' blocking method')
            else:
                logger.warning('Not implemented synthesis: ' + str(mode))

    resblocker.commitclose()

