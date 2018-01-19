import zipfile
import xml.etree.ElementTree
import io
import urllib.parse


class RknDumpParser:
    """
    RKN dump parser.
    """

    _dumpfile = None
    _datamapping = {}

    def __init__(self, dumpfile, datamapping):
        """
        :param dumpfile: binary loaded file in ram
        :param datamapping: hashmap lika 'blocktype' -> 'output filename'
        """
        self._dumpfile = dumpfile
        self._datamapping = datamapping

    # IDNA encoding can fail for too long labels (>63 characters)
    # See: https://en.wikipedia.org/wiki/Internationalized_domain_name
    def _punencodedom(self, urlstr):
        return urlstr.encode('idna').decode()

    def _punencodeurl(self, urlstr):
        urlsplit = urllib.parse.urlsplit(urlstr)
        if not urlsplit.scheme in ['http', 'https', '']:
            scheme = ''
        else:
            scheme = urlsplit.scheme
        return scheme + '://' + \
            self._punencodedom(urllib.parse.urlsplit(urlstr).netloc) + \
            urllib.parse.urlsplit(urlstr).path

    def parse(self):
        """
        Parses xml from binary dump has been loaded on init.
        Has much hardcode caused by shitty dump format
        :return: parsed entries count
        """
        xmldump = zipfile.ZipFile(io.BytesIO(self._dumpfile)).read('dump.xml')

        xmlroot = xml.etree.ElementTree.XML(xmldump)

        outfiledesc = {fname: open(file=fname, mode='w', buffering=1)
                    for fname in set(self._datamapping.values())}

        outfiles = {dtype: outfiledesc[self._datamapping[dtype]]
                    for dtype in self._datamapping}

        outdata = {dtype: set() for dtype in self._datamapping}

        count = 0
        for content in xmlroot.iter('content'):
            count += 1
            if not 'blockType' in content.attrib or \
                    content.attrib['blockType'] == 'default':
                for url in content.iter('url'):
                    if url is not None:
                        if str(url.text).find('https') < 0:
                            outdata['http'].add(
                                self._punencodeurl(url.text))
                        else:
                            outdata['https'].add(
                                self._punencodeurl(url.text))
            elif content.attrib['blockType'] == 'domain':
                dom = content.find('domain')
                if dom is not None:
                    outdata['domain'].add(
                        self._punencodedom(dom.text))
            elif content.attrib['blockType'] == 'domain-mask':
                dommsk = content.find('domain')
                if dommsk is not None:
                    outdata['domainmask'].add(
                        self._punencodedom(dommsk.text))
            elif content.attrib['blockType'] == 'ip':
                for iptag in content.iter('ip'):
                    outdata['ip'].add(iptag.text)
                for ipsubntag in content.iter('ipSubnet'):
                    outdata['ipsub'].add(ipsubntag.text)

        for datakey in outdata:
            outfiles[datakey].write('\n'.join(outdata[datakey]) + '\n')

        for openedfile in outfiles:
            outfiles[openedfile].close()

        return count