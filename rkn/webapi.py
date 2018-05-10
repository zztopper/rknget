import cgi
import json
from dbconn import connstr

def main():
    fields = cgi.FieldStorage()
    print("Content-type:application/json\r\n\r\n")
    __import__(fields['module'])
    print(json.dumps(fields['method'](connstr)))
    return 0


if __name__ == "__main__":
    result = main()
    exit(code=result)