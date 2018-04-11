from rkn.db.blockdata import BlockData


def __getBlockedDataSet(connstr, entityname):
    """
    Function for debug purposes
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: entities set
    """
    return BlockData(connstr).getBlockedResourcesSet(entityname)


def getBlockedIpSet(connstr):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: ip list
    """
    return BlockData(connstr).getBlockedResourcesSet('ip')


def getBlockedSubnetSet(connstr):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: ip/sub list
    """
    return BlockData(connstr).getBlockedResourcesSet('ipsubnet')


def getBlockedDomainsCleared(connstr):
    """
    We don't need to block domains if the same wildcard domain is blocked
    We don't need to block 3-level wildcard if 2-level wildcard is blocked
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: 2 sets: domains and wildcard domains
    """
    bldt = BlockData(connstr)
    domains = bldt.getBlockedResourcesSet('domain')
    wdomains = bldt.getBlockedResourcesSet('domain-mask')

    # Dedupe wdomains
    wds = wdomains.copy()
    for wd in wds:
        w = '.' + wd
        for wdom in wds:
            if w in wdom:
                # Using discard to ignore redelete.
                wdomains.discard(wdom)

    # Dedupe domains with wdomains
    wds = {'.'+w for w in wdomains}
    for dom in domains.copy():
        for wd in wds:
            if wd in dom:
                domains.discard(dom)

    return domains, wdomains
