import requests
from uuid import uuid1
from ConfigParser import ConfigParser
import json, hashlib, math, time, threading, sys
from os.path import dirname, abspath, join, exists, splitext, split

AUTH_REQ_TIMEOUT = 3
class Authentication(object):

    @staticmethod
    def regist(url, session_info, **kwargs):
        '''
        regist session on server
        ##session_id, token, session_info
        session info        { 'subc':'create',
                              'data':{'planname':'test.plan',
                                      'starttime':reporttime(),
                                      'deviceinfo':{'product':kwargs['product'],
                                                    'revision':kwargs['revision'],
                                                    'deviceid':kwargs['deviceid']
                                                   }
                                     }
                            }
        '''
        values = json.dumps(session_info)
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        r = request(method='post', url=url, data=values, headers=headers, timeout=AUTH_REQ_TIMEOUT)
        return r

    @staticmethod
    def getToken(url, username, password, appid='01', **kwargs):
        '''
        Get the session token from server.
        '''
        ret = None
        m = hashlib.md5()
        m.update(password)
        pwd = m.hexdigest()
        values = json.dumps({'appid':'01', 'username':username, 'password':pwd})
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        r = request(method='post', url=url, data=values, headers=headers, timeout=AUTH_REQ_TIMEOUT)
        return r and r['data']['token'] or None

AUTH_REQ_TIMEOUT = 3

def request(method, url, data=None, **kwargs):
    '''
    Sends a request.
    :param url: URL for the request.    
    :param method: the request type of http method(get, post, put, delete)
    :param data: (optional) Dictionary, bytes, or file-like object to send in the body of http protocol
    :param \*\*kwargs: Optional arguments that request takes
    :return: dict or None 
    '''
    ret = None
    m = method.lower()
    if m in ('get', 'post', 'put', 'delete'):
        req = getattr(requests, m, None)
    try:
        #ret = req(url=url, data=data, **kwargs).json()
        sys.stderr.write('begin to request token\n')
        r = req(url=url, data=data, **kwargs)
        sys.stderr.write(str(r))
        sys.stderr.write('end to request token')
        if r:
            ret = r.json()
            sys.stderr.write(str(ret))
    except requests.exceptions.Timeout, e:
        sys.stderr.write(str(e))
    except requests.exceptions.TooManyRedirects , e:
        sys.stderr.write(str(e))
    except requests.exceptions.RequestException , e:
        sys.stderr.write(str(e))
    except Exception, e:
        sys.stderr.write(str(e))
    return ret

class ReportClient(object):
    '''
    client to communicate with server
    '''
    def __init__(self, config=None, **kwargs):
        '''
        init with server.config
        '''
        self.__dict__.update(kwargs)
        self.config = config
        self.active = False
        self.token = None

    def regist(self, **kwargs):
        '''
        get token from server by server.config or user-input
        '''
        import sys
        sys.stderr.write('regist----------------------------------------------------------->>\n')
        sys.stderr.write(self.__dict__['username']+'\n')
        sys.stderr.write(self.__dict__['password']+'\n')
        sys.stderr.write(self.__dict__['auth']+'\n')

        m = hashlib.md5()
        m.update(self.__dict__['password'])
        pwd = m.hexdigest()
        #values = json.dumps({'subc': 'login', 'data':{'appid':'01', 'username':self.__dict__['username'], 'password':pwd}})
        values = json.dumps({'appid':'01', 'username':self.__dict__['username'], 'password':pwd})
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        auth_url = self.__dict__['auth']
        ret = request(method='post', url=auth_url, data=values, headers=headers, timeout=AUTH_REQ_TIMEOUT)
        sys.stderr.write(str(ret)+'\n')
        token = ret['results']['token']
        sys.stderr.write('token----------------------------------------------------------->>\n')
        sys.stderr.write(str(ret)+'\n')
        if token and not self.active:
            self.token = token
            self.active = True
        return self.active

    def createSession(self, **kwargs):
        values = json.dumps(kwargs)
        headers = {'content-type': 'application/json', 'accept': 'application/json'}

        r = request(method='post', url=url, data=values, headers=headers, timeout=AUTH_REQ_TIMEOUT)

    def createTestCase(self, **kwargs):
        pass
    
    def updateTestCase(self, **kwargs):
        pass

    def updateSession(self, **kwargs):
        pass

#client = ReportClient()