import yaml
import time
import math

class RknUpdateState:

    checkTime = 0
    downlTime = 0
    urlsCount = 0
    dumpTime  = 0
    dumpTimeU = 0

    def __init__(self, stateFilename):
        self._stateFilename = stateFilename
        self.checkTime = math.ceil(time.time() * 1000)
        try:
            stateParsed = yaml.load(stateFilename)
            self.downlTime = stateParsed['Run']['downlTime']
            self.urlsCount = stateParsed['Run']['urlsCount']
            self.downlTime = stateParsed['Dump']['dumpTime' ]
            self.urlsCount = stateParsed['Dump']['dumpTimeU']
        except:
            pass
        self._save()

    def updateTimeStamps(self, lastDumpDate, lastDumpDateUrgently):

        self.dumpTime = lastDumpDate
        self.dumpTimeU = lastDumpDateUrgently
        self._save()

    def updateInfoOnParse(self, urlsCount):
        self.downlTime = math.ceil(time.time() * 1000)
        self.urlsCount = urlsCount
        self._save()

    def _save(self):
        stateDump = dict()
        stateDump['Run'] = {
            'checkTime': self.checkTime,
            'downlTime': self.downlTime,
            'urlsCount': self.urlsCount
        }
        stateDump['Dump'] = {
            'dumpTime' : self.dumpTime,
            'dumpTimeU': self.dumpTimeU
        }
        yaml.dump(stateDump, open(file=self._stateFilename, mode='w+'), default_flow_style=False)


