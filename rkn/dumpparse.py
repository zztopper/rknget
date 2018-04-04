import zipfile
import xml.etree.ElementTree
import io

import rkn.util
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

    if xmlroot is None:
        raise RKNDumpFormatException("Parse error: no incorrect dump!")

    counter = 0

    # Getting IDs set
    outerIDSet = dbhandler.getOuterIDSet()

    # Creating new dump info record
    dump_id = dbhandler.addDumpInfoRecord(**xmlroot.attrib)

    # Filling tables
    for content in xmlroot.iter('content'):
        # We needn't operate the data which is already in the DB.
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
        content_id = dbhandler.addContent(dump_id, decision_id, **content.attrib)

        # resourses parsing...
        for tag in ('url', 'domain', 'ip', 'ipSubnet'):
            for element in content.iter(tag):
                if tag == 'url':
                    if str(element.text).find('https') < 0:
                        entitytype = 'http'
                    else:
                        entitytype = 'https'
                    value = rkn.util.urlHandler(element.text)
                elif tag == 'domain':
                    if str(element.text).find('.*') == 0:
                        entitytype = 'domain-mask'
                        # Truncating .*
                        value = rkn.util.punencodedom(_domainCorrect(element.text)[2:])
                    else:
                        entitytype = 'domain'
                        value = rkn.util.punencodedom(_domainCorrect(element.text))
                elif tag == 'ip':
                    if not rkn.util.isip(element.text):
                        continue
                    entitytype = 'ip'
                    value = element.text
                elif tag == 'ipSubnet':
                    if not rkn.util.isipsub(element.text):
                        continue
                    entitytype = 'ipsubnet'
                    value = element.text

                dbhandler.addResource(content_id=content_id,
                                          last_change=element.attrib.get('ts'),
                                          entitytype=entitytype,
                                          value=value)

        counter += 1
        if counter % 1000 == 0:
            print("Parsed: " + str(counter))
            # dbhandler._session.commit()

    # There are content rows have been removed remain.
    if len(outerIDSet) > 0:
        dbhandler.updateContentPresence(dump_id, outerIDSet)
    # Set dump entry parsed.
    dbhandler.setDumpParsed(dump_id)

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

