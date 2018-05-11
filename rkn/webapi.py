#!/usr/bin/env python3
import cgi
import json

from dbconn import connstr


def _getParamsDict():
    fields = cgi.FieldStorage()
    return {key: fields.getvalue(key) for key in fields.keys()}


def main():
    fields = _getParamsDict()
    modval = fields.pop('module', None)
    metval = fields.pop('method', None)
    rawval = fields.pop('raw', None)
    module = __import__(modval, fromlist=[metval])
    fields['connstr'] = connstr
    # Shoot your leg through!!!
    data = getattr(module, metval)(**fields)

    if rawval in ('True', '1', 'yes', 'true', 'OK'):
        print("Content-Type: text/plain\r\n\r\n")
        print(str(data))
    else:
        print("Content-type:application/json\r\n\r\n")
        print(json.dumps(data, default=str))

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
