#!/usr/bin/env python3
import cgi
import json
from dbconn import connstr

def main():
    fields = cgi.FieldStorage()
    print("Content-type:application/json\r\n\r\n")
    module = __import__(fields.getvalue('module'))

    print(
        json.dumps(
            getattr(module,
                    fields.getvalue('method'))
            (connstr)
        )
    )
    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)