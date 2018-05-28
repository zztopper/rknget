#!/usr/bin/env python3
import cgi

from dbconn import connstr

"""
Provides the data for HTTP Content Sensor
"""
def _getParamsDict():
    fields = cgi.FieldStorage()
    return {key: fields.getvalue(key) for key in fields.keys()}


def main():
    fields = _getParamsDict()
    modval = fields.pop('module', None)
    if modval.split('.')[0] != 'api':
        print('Content-Type: text/plain\r\n\r\nNot an API')
        return 1
    metval = fields.pop('method', None)
    module = __import__(modval, fromlist=[metval])
    fields['connstr'] = connstr

    # Shoot your leg through!!!
    data = getattr(module, metval)(**fields)
    try:
        result = ''.join('[' + str(d) + ']' for d in data)
    except TypeError:
        result = '[' + str(data) + ']'

    print("Content-Type: text/plain\r\n\r\n")
    print(result)

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
