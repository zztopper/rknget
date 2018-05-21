import urllib.parse
import re
import ipaddress


def punencodedom(urlstr):
    """
    IDNA encoding can fail for too long labels (>63 characters)
    See: https://en.wikipedia.org/wiki/Internationalized_domain_name
    """
    return urlstr.encode('idna').decode()


def getdomain(urlstr):
    return urllib.parse.urlparse(urlstr).netloc.split(':')[0].lower()


# More goddamn hardcode to the Hardcode God!
def urlHandler(urlstr):
    parsedUrl = urllib.parse.urlparse(urlstr)
    # Erroneous proto is assumed to be http.
    if parsedUrl[0] != 'http' and parsedUrl[0] != 'https':
        parsedUrl[0] = 'http'
    domain = parsedUrl.netloc.split(':')[0]
    if parsedUrl.netloc.find(':') != -1:
        port = ':' + parsedUrl.netloc.split(':')[1]
    else:
        port = ''
    punedomain = punencodedom(domain)

    # Some magic with url parts after domain
    urlmap = map(
        lambda urlpart, char:
            char + urllib.parse.quote(string=urlpart, safe=''':/?#[]@!$&'()*+,;=%''')
            if urlpart != '' else '',
        parsedUrl[2:], ['', ';', '?', '#']
    )
    # pathEncoded = '/' + urllib.parse.quote(string=parsedUrl.path, safe='~@#$&()*!+=:;,.?/\%\\') \
    #     if parsedUrl.path != '' else ''
    # parmEncoded = url   lib.parse.quote(string=parsedUrl.params, safe='~@#$&()*!+=:;,.?/\%\\')
    # querEncoded = urllib.parse.quote(string=parsedUrl.query,  safe='~@#$&()*!+=:;,.?/\%\\')
    # fragEncoded = urllib.parse.quote(string=parsedUrl.fragment,  safe='~@#$&()*!+=:;,.?/\%\\')

    return parsedUrl[0] + '://' + punedomain + port + ''.join(list(urlmap))


def domainCorrect(s):
    """
    Corrects given domain.
    :param s: str
    :return: corrected domains
    """
    badchars = ('\\', '\'', '"')
    for c in badchars:
        if s.find(c) != -1:
            s = ''.join(s.split(c))
    return s


# Robust, but 5 times slower
def _isip(s):
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


# Robust, but 5 times slower
def _isipsub(s):
    try:
        ipaddress.ip_network(s)
        return True
    except ValueError:
        return False


__ipregex = re.compile('''\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}''')


def isip(s):
    return __ipregex.fullmatch(s) is not None


def isipsub(s):
    try:
        ip, sub = s.split('/')
        if int(sub) <= 32 and isip(ip):
            return True
    except:
        return False


__domregex = re.compile('''^.+\..*[^.]$''')


def isdomain(s):
    return __domregex.fullmatch(s) is not None


def isprivate(s):
    try:
        return ipaddress.ip_network(s).is_private
    except ValueError:
        return False


def getSubnetIPs(s):
    try:
        return ipaddress.ip_network(s).hosts()
    except ValueError:
        return None
