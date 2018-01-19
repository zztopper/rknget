import zeep.client
import time
import xml.etree.ElementTree


class RknSOAPWrapper:

    _rknsoapclient = None
    _retryAttempts = 5
    _sleeptimeout = 60
    _dumpFmtVersion = '2.3'

    def __init__(self, url, retrycount=5, sleeptimeout=60, dumpfmtver=2.3, **kwargs):

        self._rknsoapclient = zeep.client.Client(wsdl=url)
        self._rknsoapclient.options(raw_response=True)
        try:
            self._retryAttempts = retrycount
            self._sleeptimeout = sleeptimeout
            self._dumpFmtVersion = str(dumpfmtver)
        except KeyError:
            pass

    def _wsdlCall(self, method, **kwargs):
        """Makes WSDL request
        :return: xml response or None if failed
        """
        i = 0
        while i < self._retryAttempts:
            try:
                sp = self._rknsoapclient.service[method]
                if len(kwargs):
                    response = sp(**kwargs)
                else:
                    response = sp()
                if response:
                    return response
            except Exception as e:
                i += 1
                time.sleep(self._sleeptimeout)

        # if i >= self._retryAttempts:
        return None

    def getLastDumpDateEx(self):
        """Obtains RKN dump state info
        :return: dict {lastDumpDate: UTS (ms), lastDumpDateUrgently: UTS (ms)}
        """
        return (self._wsdlCall('getLastDumpDateEx'))

    def getDumpFile(self, reqFileBase64, sigFileBase64):
        """Obtains RKN dump code
        Loads dump file
        :return: dump file zipped
        """

        dumpReqAnswer = self._wsdlCall('sendRequest',
                                       requestFile=reqFileBase64,
                                       signatureFile=sigFileBase64,
                                       dumpFormatVersion=self._dumpFmtVersion
                                       )
        if not dumpReqAnswer['result']:
            raise Exception('Couldn\'t send a request, reason: ' + dumpReqAnswer['resultComment'])

        i = 0
        while i < self._retryAttempts:
            resultAnswer = self._wsdlCall('getResult', code=dumpReqAnswer['code'])
            if not resultAnswer['result'] and resultAnswer['resultCode'] == 0:
                i += 1
                time.sleep(self._sleeptimeout)
            else:
                break
        if not resultAnswer['result']:
            raise Exception('Couldn\'t process a request, reason: ' + dumpReqAnswer['resultComment'])

        return resultAnswer['registerZipArchive']