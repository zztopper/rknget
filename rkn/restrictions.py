from rkn.db.blockdata import BlockData

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
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: 2 sets: domains and wildcard domains
    """
    bldt = BlockData(connstr)
    domains = bldt.getBlockedResourcesSet('domain')
    wdomains = bldt.getBlockedResourcesSet('domain-mask')

    # Dedupe wd
    for wd in wdomains:
        w = '.' + wd
        for wdom in wdomains:
            if wdom.find(w) != -1:
                wdomains.pop(wdom)

    # Dedupe domains with wd
    for wd in wdomains:
        w = '.' + wd
        for dom in domains:
            if dom.find(w) != -1:
                wdomains.pop(dom)

    return domains, wdomains
