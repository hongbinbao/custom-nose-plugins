import requests
from uuid import uuid1
from ConfigParser import ConfigParser
import json, hashlib, math, time, threading, sys
from os.path import dirname, abspath, join, exists, splitext, split

AUTH_REQ_TIMEOUT = 3
REQ_TIMEOUT = 3
#Unused. support upload result to remote server with below API in future.

###authentication###
#method: POST
#request URI      : http://ats.borqs.com/smartapi/account/login
#request header   : Content-Type: 'application/json', 'Accept': 'application/json'
#request payload  : {'subc': 'login',
#                   'data': {appid': 01, 'username': username, 'password': pwd}

#response payload : {'result': ok|error, 'data': {'token': token}, 'msg': log_error}





###test session create###
#method: POST
#request URI      : http://ats.borqs.com/smartapi/group/<group_id>/test/<session_id>/create
#request header   : Content-Type: 'application/json', 'Accept': 'application/json'
#request payload  : { 'subc': 'create',
#                     'data':{ 'token': token,
#                              'planname': plan_name,
#                              'starttime': session_start_time,
#                              'deviceinfo':{'product': product_name,
#                                            'revision': product_revision,
#                                            'deviceid': device_serial_number
#                                           }
#                            }
#                    }

#response payload : {'result': ok|error, msg': log_error}

###create test case###
#method: POST
#request URI      : http://ats.borqs.com/smartapi/group/<group_id>/test/<session_sid>/case/<tid>/create
#request header   : Content-Type: 'application/json', 'Accept': 'application/json'
#request payload  : {'tid':tid, 'sid':session_id, 'casename': domain.case_name), 'starttime': case_start_time}}
#response payload : {'result': ok|error, msg': log_error}

###update test case###
#method: POST
#request URI      : http://ats.borqs.com/smartapi/group/<group_id>/test/<session_id>/case/<tid>/update
#request header   : Content-Type: 'application/json', 'Accept': 'application/json'
#request payload  : {'tid':tid, 'result': pass|fail|error|timeout, 'time': case_end_time, 'traceinfo': trace_stack_output}
#response payload : {'result': ok|error, msg': log_error}

###upload file###
#method: PUT
#request URI      : http://ats.borqs.com/smartapi/group/<group_id>/test/<session_id>/case/<tid>/fileupload
#request header   : Content-Type: 'image/png' | Content-Type: 'application/zip', 'Accept': 'application/json'
#request payload  : {'file': file_data }
#response payload : {'result': ok|error, msg': log_error}


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
        '''
        session_properties = {    'sid': self.session_id,\
                                  'product': 'p',\
                                  'revision': 'r',\
                                  'deviceid': 'devid',\
                                  'planname': 'test.plan',\
                                  'starttime': self.conf.test_start_time
                                 }
        '''
        url = self.__dict__['session_create'] % kwargs.pop('sid')
        
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        #new style API
        #values = { 'token': self.token,\
        #           'subc':'create',\
        #           'data':{'planname':kwargs.pop('planname'),\
        #                   'starttime':kwargs.pop('starttime'),\
        #                   'deviceinfo':{'product':kwargs.pop('product'),\
        #                   'revision':kwargs.pop('revision'),\
        #                   'deviceid':kwargs.pop('deviceid')\
        #                                }\
        #                  }\
        #          }
        deviceinfo = {'product':kwargs.pop('product'), 'revision':kwargs.pop('revision'), 'width':'320', 'height':'480'}
        values = {'token': self.token, 'planname':kwargs.pop('planname'),'starttime':kwargs.pop('starttime'),'deviceid':kwargs.pop('deviceid'),'deviceinfo':deviceinfo}
        values = json.dumps(values)
        r = request(method='post', url=url, data=values, headers=headers, timeout=REQ_TIMEOUT)
        sys.stderr.write('session----------------------------------------------------------->>\n')
        sys.stderr.write(str(r)+'\n')

    def createTestCase(self, **kwargs):
        sys.stderr.write('case------------------------------cccccccccccc----------------------------->>\n')
        url = self.__dict__['case_create'] % (kwargs.pop('sid'), kwargs.pop('tid'))
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        values = json.dumps(kwargs.update({'token': self.token}))        
        r = request(method='post', url=url, data=values, headers=headers, timeout=REQ_TIMEOUT)
        sys.stderr.write('case----------------------------------------------------------->>\n')
        sys.stderr.write(str(r)+'\n')

    def updateTestCase(self, **kwargs):
        pass

    def updateSession(self, **kwargs):
        pass

class UploadThread(threading.Thread):
    '''
    Thread for uploading result.
    '''
    def __init__(self, session_id, token, cycle_id, path, callback=None):
        '''
        Init the instance of Sender.
        '''
        super(UploadThread, self).__init__(name='%s%s'%('upload-',str(cycle_id)))
        #self.daemon = True
        self._is_stop = False

    def run(self):
        '''
        The work method.
        '''
        try:
            pass
        except Exception, e:
            logger.debug(str(e))
            self.stop()
        finally:
            if self._callback: self._callback()

    def stop(self):
        '''
        Stop the thread.
        '''
        self.is_stop = True

#client = ReportClient()