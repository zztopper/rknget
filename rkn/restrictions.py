from rkn.db.blockdata import BlockData
import re
import ipaddress

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
        regex = re.compile('''^.+\.''' + wd + '''$''')
        for wdom in wds:
            if regex.fullmatch(wdom):
                # Using discard to ignore redelete.
                wdomains.discard(wdom)

    # Dedupe domains with wdomains
    for wd in wdomains.copy():
        regex = re.compile('''^(.*[^.]\.)?''' + wd + '''$''')
        for dom in domains.copy():
            if regex.fullmatch(dom):
                # Using discard to ignore redelete.
                domains.discard(dom)

    return domains, wdomains
