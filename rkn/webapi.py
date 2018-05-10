#!/usr/bin/env python3
import cgi
import json
from dbconn import connstr


def _getParamsDict():
    fields = cgi.FieldStorage()
    return {key: fields.getvalue(key) for key in fields.keys()}


def main():
    fields = _getParamsDict()
    modval = fields.pop('module')
    metval = fields.pop('method')

    print("Content-type:application/json\r\n\r\n")
    module = __import__(modval, fromlist=[metval])
    fields['connstr'] = connstr

    print(
        json.dumps(
            getattr(module, metval)
            (**fields)
        )
    )
    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
