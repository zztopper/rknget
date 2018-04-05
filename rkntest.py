#!/usr/bin/env python3


import rknget
from rkn import rknstatehandler, rknsoapwrapper, dumpparse



def main():
    config = rknget.initConf()
    logger = rknget.initLog(config['Logging']['logpath'], 'DEBUG', 'DEBUG')
    logger.debug('Test module started')
    logger.debug('Using stateless mode')
    if not config['Debug']['useTempData']:
        if not config['Debug']['useTempDump']:
            dumpFile = rknsoapwrapper.RknSOAPWrapper(**config['DumpLoader'])\
                .getDumpFile(open(config['Global']['reqPath'], 'rb').read(),
                             open(config['Global']['reqPathSig'], 'rb').read()
                             )
            if config['Global']['savetmp']:
                open(file=config['Global']['tmppath']+'/dump.xml.zip', mode='wb').write(dumpFile)
        else:
            dumpFile = open(config['Global']['tmppath']+'/dump.xml.zip', mode='rb').read()
            connstr = rknget.buildConnStr(**config['DB'])
        outdata = dumpparse.parse(dumpFile, connstr)
        del dumpFile
    else:
        pass

    logger.info('Parsed data have been saved')
  

if __name__ == "__main__":
    main()
