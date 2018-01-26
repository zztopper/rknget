import zipfile
import xml.etree.ElementTree
import io
import urllib.parse

datatypes = (
    'http',
    'https',
    'domain',
    'domainmask',
    'ip',
    'ipsub'
)


# IDNA encoding can fail for too long labels (>63 characters)
# See: https://en.wikipedia.org/wiki/Internationalized_domain_name
def _punencodedom(urlstr):
    return urlstr.encode('idna').decode()


def _getdomain(urlstr):
    return urllib.parse.urlparse(urlstr).netloc.split(':')[0]

# More goddamn hardcode to the Hardcode God!
def _urlHandler(urlstr):
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
    punedomain = _punencodedom(domain)

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

    return punedomain + port + ''.join(list(urlmap))


def _asterize(s):
    """
    Adds asterisk (*) to the start and to the end of the string,
    but not repeating the sign.
    Special cases:
    '' -> ''
    :param string: str
    :return: string complemented by asterisks
    """
    if len(s) == 0:
        return ''
    if s[0] == '*':
        if s[-1] == '*':
            return s
        else:
            return s + '*'
    elif s[-1] == '*':
        return '*' + s
    return '*' + s + '*'


def parse(dumpfile):
    """
    :param dumpfile: binary loaded file in ram
    Parses xml from binary dump has been loaded on init.
    Has much hardcode caused by shitty dump format
    :return: data divided on groups defined on the top

    """
    xmldump = zipfile.ZipFile(io.BytesIO(dumpfile)).read('dump.xml')

    xmlroot = xml.etree.ElementTree.XML(xmldump)

    outdata = {datatype: set() for datatype in datatypes}

    count = 0
    for content in xmlroot.iter('content'):
        count += 1
        if not 'blockType' in content.attrib or \
                content.attrib['blockType'] == 'default':
            for url in content.iter('url'):
                if url is not None:
                    if str(url.text).find('https') < 0:
                        # Blocking only single URL
                        outdata['http'].add(
                            _asterize(
                                _urlHandler(url.text)))
                    else:
                        # Blocking all domain
                        outdata['https'].add(
                            _asterize(
                                _punencodedom(
                                    _getdomain(url.text))))
        elif content.attrib['blockType'] == 'domain':
            dom = content.find('domain')
            if dom is not None:
                outdata['domain'].add(
                    _punencodedom(dom.text))
        elif content.attrib['blockType'] == 'domain-mask':
            dommsk = content.find('domain')
            if dommsk is not None:
                outdata['domainmask'].add(
                    _punencodedom(dommsk.text))
                outdata['https'].add(
                    _asterize(
                        _punencodedom(dommsk.text)))
        elif content.attrib['blockType'] == 'ip':
            for iptag in content.iter('ip'):
                outdata['ip'].add(iptag.text)
            for ipsubntag in content.iter('ipSubnet'):
                outdata['ipsub'].add(ipsubntag.text)

    return outdata
