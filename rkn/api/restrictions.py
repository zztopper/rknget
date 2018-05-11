from db.blockdata import BlockData
import re
import ipaddress

"""
This module only operates with Resources data
I had to switch returned datasets to list to make those json serialisable
"""


def _getBlockedDataList(connstr, entityname):
    """
    Function for debug purposes
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: entities set
    """
    return list(BlockData(connstr).getBlockedResourcesSet(entityname))


def getBlockedHTTP(connstr):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return URLs strings list
    """
    return list(BlockData(connstr).getBlockedResourcesSet('http'))


def getBlockedHTTPS(connstr):
    """
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return URLs strings list
    """
    return list(BlockData(connstr).getBlockedResourcesSet('https'))


def getBlockedIPsFromSubnets(connstr):
    """
    Explodes restricted ip subnets into IP list.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: IP list.
    """
    ipsubs = {ipaddress.ip_network(addr)
              for addr in BlockData(connstr).getBlockedResourcesSet('ipsubnet')}

    return [str(host) for ipsub in ipsubs for host in ipsub.hosts()]


def getBlockedIPsMerged(connstr):
    """
    Merges IPs into IP subnets containing first ones.
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    :return: The total and the list of ip subnets, using /32 for ips.
    """
    bldt = BlockData(connstr)
    ips = [ipaddress.ip_network(addr) for addr in bldt.getBlockedResourcesSet('ip')]
    ipsubs = [ipaddress.ip_network(addr) for addr in bldt.getBlockedResourcesSet('ipsubnet')]
    ipsall = ips + ipsubs
    return [list(map(str, ipaddress.collapse_addresses(ipsall))),
            sum(map(lambda x: x.num_addresses, ipsall))]


def getBlockedDomainsMerged(connstr):
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

    return [list(domains), list(wdomains)]
