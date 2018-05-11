import json
import base64
import ssl
import urllib.parse
from http.client import HTTPConnection, HTTPSConnection


def _base64httpcreds(user, password):
    # Encoding 'user:password' string to base64 and then to ASCII string back.
    return base64.b64encode((str(user) + ':' + str(password)).encode()).decode('ascii')


def call(host, port, secure, url,
            module, method,
            timeout=60, user=None, password=None,
            **params):
    """
    Gets data from webserver by webapi.
    The syntax is pretty simple.
    :param host: hostname or ip
    :param port: webservice port
    :param secure: if ssl is enabled, is it?
    :param timeout: recommended to be enough for data processing on the server
    :param user: http server authorisation credentials
    :param password: http server authorisation credentials
    :param url: the path to rkn/webapi.py executive
    :param module - module name like api.smth
    :param method - method name in the module
    :param params - method params
    RTFM if exists
    :return: everything you could expect or not ;-)
    """
    params['module'] = module
    params['method'] = method

    if secure:
        conn = HTTPSConnection(host=host, port=port, timeout=timeout,
                               context=ssl._create_unverified_context())
    else:
        conn = HTTPConnection(host=host, port=port, timeout=timeout)

    headers = {'Accept': 'text/plain'}
    if None not in (user, password):
        headers['Authorization'] = 'Basic ' + _base64httpcreds(user, password)

    conn.request(method='POST',
                 url=url,
                 body=urllib.parse.urlencode(params),
                 headers=headers
                 )

    resp = conn.getresponse()
    if resp.code != 200:
        raise Exception('WebAPI response code: ' + str(resp.code))
    return json.loads(resp.read())
