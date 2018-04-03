import urllib.parse
import re


def punencodedom(urlstr):
    return urlstr.encode('idna').decode()


def getdomain(urlstr):
    return urllib.parse.urlparse(urlstr).netloc.split(':')[0]


# More goddamn hardcode to the Hardcode God!
def urlHandler(urlstr):
    """
    Common rules:
        - proto, colon, two slashes are trunkated | http://, https://
        - % sign is considered to be already encoded
        - result is complemented by asterisks | *...*
    :return:
    """
    parsedUrl = urllib.parse.urlparse(urlstr)
    domain = parsedUrl.netloc.split(':')[0]
    if parsedUrl.netloc.find(':') != -1:
        port = ':' + parsedUrl.netloc.split(':')[1]
    else:
        port = ''
    punedomain = punencodedom(domain)

    # Some magic with url parts after domain
    urlmap = map(
        lambda urlpart, char:
            char + urllib.parse.quote(string=urlpart, safe='~@#$&()*!+=:;,.?/\%\\')
            if urlpart != '' else '',
        parsedUrl[2:], ['', ';', '?', '#']
    )
    # pathEncoded = '/' + urllib.parse.quote(string=parsedUrl.path, safe='~@#$&()*!+=:;,.?/\%\\') \
    #     if parsedUrl.path != '' else ''
    # parmEncoded = urllib.parse.quote(string=parsedUrl.params, safe='~@#$&()*!+=:;,.?/\%\\')
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


__ipregex = re.compile('''\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}''')


def isip(s):
    return __ipregex.match(s) is not None


def isipsub(s):
    try:
        ip, sub = s.split('/')
        if int(sub) <= 32 and isip(ip):
            return True
    except:
        return False