import zipfile
import xml.etree.ElementTree
import io

import rkn.util
from rkn.db.dataprocessing import DataProcessor


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
    dataproc = DataProcessor(connstr)

    if xmlroot is None:
        raise RKNDumpFormatException("Parse error: no incorrect dump!")

    counter = 0

    # Getting IDs set
    outerIDSet = dataproc.getOuterIDSet()

    # Creating new dump info record
    dump_id = dataproc.addDumpInfoRecord(**xmlroot.attrib)

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
        decision_id = dataproc.addDecision(**des.attrib) #date, number, org

        # Importing content
        content_id = dataproc.addContent(dump_id, decision_id, **content.attrib)

        # resourses parsing...
        # walking through the available tags
        for tag in ('url', 'domain', 'ip', 'ipSubnet'):
            for element in content.iter(tag):
                if tag == 'url':
                    if str(element.text).find('https') < 0:
                        entitytype = 'http'
                    else:
                        entitytype = 'https'
                    value = rkn.util.urlHandler(element.text)
                elif tag == 'domain':
                    # Why wouldn't be used content.attrib['blockType'] instead?
                    # Because domain tags don't depend on content blocktype.
                    if not rkn.util.isdomain(element.text):
                        continue
                    if str(element.text).find('*.') == 0:
                        entitytype = 'domain-mask'
                        # Truncating *.
                        value = rkn.util.punencodedom(
                            rkn.util.domainCorrect(element.text)[2:])
                    else:
                        entitytype = 'domain'
                        value = rkn.util.punencodedom(
                            rkn.util.domainCorrect(element.text))
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

                dataproc.addResource(content_id=content_id,
                                          last_change=element.attrib.get('ts'),
                                          entitytype=entitytype,
                                          value=value)

        counter += 1
        if counter % 100 == 0:
            print("Parsed: " + str(counter))
            # dataproc._session.commit()

    # There are content rows have been removed remain.

    dataproc.updateContentPresence(dump_id, outerIDSet)
    # Set dump entry parsed.
    dataproc.setDumpParsed(dump_id)

    dataproc.commitclose()
