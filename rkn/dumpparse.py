import zipfile
import xml.etree.ElementTree
import io
import urllib.parse
import re
from datetime import date, datetime
from rkn.db.dataproc import DatabaseHandler


class RKNDumpFormatException(BaseException):
    pass


#class RKNDumpFormatException(Exception):
#    def __init__(self, message, errors):
#        # Call the base class constructor with the parameters it needs
#        super().__init__(message)
#        # Now for your custom code...
#        self.errors = errors


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

    return parsedUrl[0] + '://' + punedomain + port + ''.join(list(urlmap))

def _domainCorrect(s):
    """
    Corrects given domain.
    :param s: str
    :return: corrected domain
    """
    badchars = ('\\', '\'', '"')
    for c in badchars:
        if s.find(c) != -1:
            s = ''.join(s.split(c))
    return s


__ipregex = re.compile('''\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}''')


def _isip(s):
    return __ipregex.match(s) is not None


def _isipsub(s):
    try:
        ip, sub = s.split('/')
        if int(sub) <= 32 and _isip(ip):
            return True
    except:
        return False


def parse(dumpfile, connstr):
    """
    :param dumpfile: binary loaded file in ram
    :param connstr: smth like "engine://user:pswd@host:port/dbname"
    Parses xml from binary dump has been loaded on init.
    Has much hardcode caused by shitty dump format

    """
    xmldump = zipfile.ZipFile(io.BytesIO(dumpfile)).read('dump.xml')

    xmlroot = xml.etree.ElementTree.XML(xmldump)

    dbhandler = DatabaseHandler(connstr)

    counter = 0

    # Getting IDs set
    outerIDSet = dbhandler.getOuterIDSet()

    # Filling tables
    for content in xmlroot.iter('content'):
        if int(content.attrib['id']) in outerIDSet:
            outerIDSet.remove(int(content.attrib['id']))
            continue
        # Else new content entry
        # Importing decision
        des = content.find('decision')
        if des is None:
            raise RKNDumpFormatException("Parse error: no Decision for content id: "+content.attrib['id'])
        decision_id = dbhandler.addDecision(**des.attrib) #date, number, org

        # Importing content
        content_id = dbhandler.addContent(decision_id, **content.attrib)

        # resourses parsing...
        for tag in ('url', 'domain', 'ip', 'ipSubnet'):
            for element in content.iter(tag):
                if tag == 'url':
                    if str(element.text).find('https') < 0:
                        entitytype = 'http'
                    else:
                        entitytype = 'https'
                    value = _urlHandler(element.text)
                elif tag == 'domain':
                    if str(element.text).find('.*') == 0:
                        entitytype = 'domain-mask'
                        # Truncating .*
                        value = _punencodedom(_domainCorrect(element.text)[2:])
                    else:
                        entitytype = 'domain'
                        value = _punencodedom(_domainCorrect(element.text))
                elif tag == 'ip':
                    if not _isip(element.text):
                        continue
                    entitytype = 'ip'
                    value = element.text
                elif tag == 'ipSubnet':
                    if not _isipsub(element.text):
                        continue
                    entitytype = 'ipsubnet'
                    value = element.text

                dbhandler.addResource(content_id=content_id,
                                          last_change=element.attrib.get('ts'),
                                          entitytype=entitytype,
                                          value=value,
                                          synthetic=False)

        counter += 1
        if counter % 1000 == 0:
            print("Parsed: " + str(counter))
            dbhandler._session.commit()

    # There are content rows have been removed remain.
    if len(outerIDSet) > 0:
        dbhandler.disableRemovedContent(outerIDSet)

    dbhandler.commitclose()

    # if not 'blockType' in content.attrib or \
    #         content.attrib['blockType'] == 'default':
    #     # Considered to be an url
    #     for url in content.iter('url'):
    #         if url is not None:
    #             if str(url.text).find('https') < 0:
    #                 # Blocking only single URL
    #                 outdata['http'].add(
    #                     _asterize(
    #                         _urlHandler(url.text)))
    #             else:
    #                 # Blocking all domain
    #                 outdata['https'].add(
    #                     _asterize(
    #                         _punencodedom(
    #                             _getdomain(url.text))))
    # elif content.attrib['blockType'] == 'domain':
    #     dom = content.find('domain')
    #     if dom is not None:
    #         outdata['domain'].add(
    #             _punencodedom(
    #                 _domainCorrect(dom.text)))
    # elif content.attrib['blockType'] == 'domain-mask':
    #     dommsk = content.find('domain')
    #     if dommsk is not None:
    #         outdata['domainmask'].add(
    #             _punencodedom(
    #                 _domainCorrect(dommsk.text)))
    #         outdata['https'].add(
    #             _asterize(
    #                 _punencodedom(
    #                     _domainCorrect(dommsk.text))))
    # elif content.attrib['blockType'] == 'ip':
    #     for iptag in content.iter('ip'):
    #         if _isip(iptag.text):
    #             outdata['ip'].add(iptag.text)
    #     for ipsubntag in content.iter('ipSubnet'):
    #         if _isipsub(ipsubntag.text):
    #             outdata['ipsub'].add(ipsubntag.text)

