import zipfile
import xml.etree.ElementTree
import io

import parseutils
from db.dataprocessing import DataProcessor


class RKNDumpFormatException(BaseException):
    pass


#class RKNDumpFormatException(Exception):
#    def __init__(self, message, errors):
#        # Call the base class constructor with the parameters it needs
#        super().__init__(message)
#        # Now for your custom code...
#        self.errors = errors


def getLastDumpInfo(connstr):
    return DataProcessor(connstr).getLastDumpInfo()


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

    # Getting ID:Hash dict
    outerHashes = dataproc.getOuterIDHashes()

    # Creating new dump info record
    dump_id = dataproc.addDumpInfoRecord(**xmlroot.attrib)

    # Filling tables
    for content in xmlroot.iter('content'):
        dump_outer_id = int(content.attrib['id'])
        dump_hash = content.attrib['hash']
        # BTW, we don't consider hashes in dump to be null.
        if outerHashes.get(dump_outer_id) == dump_hash:
            outerHashes.pop(dump_outer_id)
            # Don't touch the entries not having been changed
            continue
        else:
            if outerHashes.get(dump_outer_id) is not None:
                # Divergence
                dataproc.delContent(dump_outer_id)
                outerHashes.pop(dump_outer_id)
            # We've got new content entry. Importing decision
            des = content.find('decision')
            if des is None:
                raise RKNDumpFormatException("Parse error: no Decision for content id: " + content.attrib['id'])
            decision_id = dataproc.addDecision(**des.attrib)  # date, number, org
            # Importing content
            content_id = dataproc.addContent(dump_id, decision_id, **content.attrib)

        # resourses parsing...
        # walking through the available tags
        for tag in ('url', 'domain', 'ip', 'ipSubnet'):
            for element in content.iter(tag):
                if tag == 'url':
                    if str(element.text).find('https') == 0:
                        entitytype = 'https'
                    else:
                        entitytype = 'http'
                    value = rkn.parseutils.urlHandler(element.text)
                elif tag == 'domain':
                    # Why wouldn't be used content.attrib['blockType'] instead?
                    # Because domain tags don't depend on content blocktype.
                    if not rkn.parseutils.isdomain(element.text):
                        continue
                    if '*.' in str(element.text):
                        entitytype = 'domain-mask'
                        # Truncating *.
                        value = rkn.parseutils.punencodedom(
                            rkn.parseutils.domainCorrect(element.text)[2:])
                    else:
                        entitytype = 'domain'
                        value = rkn.parseutils.punencodedom(
                            rkn.parseutils.domainCorrect(element.text))
                elif tag == 'ip':
                    if not rkn.parseutils.isip(element.text):
                        continue
                    entitytype = 'ip'
                    value = element.text
                elif tag == 'ipSubnet':
                    if not rkn.parseutils.isipsub(element.text):
                        continue
                    entitytype = 'ipsubnet'
                    value = element.text

                dataproc.addResource(content_id=content_id,
                                          last_change=element.attrib.get('ts'),
                                          entitytype=entitytype,
                                          value=value)

    # There are content rows have been removed remain.

    dataproc.updateContentPresence(dump_id, set(outerHashes.keys()))
    # Set dump entry parsed.
    dataproc.setDumpParsed(dump_id)

    dataproc.commitclose()
