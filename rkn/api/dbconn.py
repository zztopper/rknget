"""
Configuration file for RKNDB API
"""

def buildConnStr(engine, host, port, dbname, user, password, **kwargs):
    return engine + '://' + \
           user + ':' + password + '@' + \
           host + ':' + str(port) + '/' + dbname

dbconn = {
    "engine": "postgresql",
    "host": "10.1.241.154",
    "port": "5432",
    "dbname": "rkndb",
    "user": "rkn",
    "password": "hry"
}

connstr = buildConnStr(**dbconn)
