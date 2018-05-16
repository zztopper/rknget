"""
Configuration file for RKNDB API
"""

def buildConnStr(engine, host, port, dbname, user, password, **kwargs):
    return engine + '://' + \
           user + ':' + password + '@' + \
           host + ':' + str(port) + '/' + dbname

dbconn = {
    "engine": "postgresql",
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "rkndb",
    "user": "rkn",
    "password": "hry"
}

connstr = buildConnStr(**dbconn)
