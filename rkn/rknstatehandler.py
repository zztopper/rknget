import yaml
import time
import math

# Base YAML schema which must be provided by the state file.
# Replaces the second one if invalid.
stateschema = {'Dump':  {},
               'Run':   {},
               'Parse': {}
               }

class RknStateHandler:

    _stateFilename = 'state.yml'
    state = {}

    def __init__(self, stateFilename):
        self._stateFilename = stateFilename
        try:
            self.state = yaml.load(open(stateFilename))
            if not all(item in stateschema for item in self.state):
                self.state.update(stateschema)
        except Exception as e:
            self.state = stateschema

        self.state['Run']['startTime'] = self._now()
        self._save()

    def updateTimeStamps(self, lastDumpDate, lastDumpDateUrgently):

        self.state['Dump']['dumpTime']  = lastDumpDate
        self.state['Dump']['dumpTimeU'] = lastDumpDateUrgently

        self.state['Run']['checkTime'] = self._now()
        self._save()

    def isActual(self):
        parseTime = self.state['Run'].get('parseTime')
        if parseTime == None:
            self.state['Run']['parseTime'] = 0
            self._save()
            return False
        if parseTime < self.state['Dump']['dumpTime'] or \
                parseTime < self.state['Dump']['dumpTimeU']:
            return False
        return True

    def updateParseInfo(self, data):
        """
        :param data to save in Parse section, None means parsing failure
        :return:
        """
        if data == None:
            self.state['Parse']['Success'] = False
        else:
            self.state['Parse']['Success'] = True
            self.state['Parse'].update(data)
        self.state['Run']['parseTime'] = self._now()
        self._save()

    def _save(self):
        yaml.dump(self.state, open(file=self._stateFilename, mode='w+'), default_flow_style=False)

    def _now(self):
        return math.ceil(time.time() * 1000)

