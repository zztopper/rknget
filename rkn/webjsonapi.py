#!/usr/bin/env python3
import json
import sys

from dbconn import connstr


def main():
    jsin = json.loads(sys.stdin.read())

    modval = jsin.pop('module', None)
    if modval.split('.')[0] != 'api':
        print('Content-Type: text/plain\r\n\r\nNot an API')
        return 1
    metval = jsin.pop('method', None)
    module = __import__(modval, fromlist=[metval])
    jsin['connstr'] = connstr

    # Shoot your leg through!!!
    data = getattr(module, metval)(**jsin)

    print("Content-type:application/json\r\n\r\n")
    print(json.dumps(data, default=str))

    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)
