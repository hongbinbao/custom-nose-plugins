#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import time
import logging
import shutil
import nose
from commands import getoutput as shell
from devicewrapper.android import device, ExpectException
from os.path import join, exists
import uuid
import subprocess
from ConfigParser import ConfigParser
from client import ReportClient

log = logging.getLogger(__name__)

TIME_STAMP_FORMAT = '%Y-%m-%d_%H:%M:%S'
TAG='----------------------**********LocalReportPlugin**************-----------------------'

def _time():
    return time.strftime(TIME_STAMP_FORMAT, time.localtime(time.time()))

def _mkdir(path):
    if not exists(path):
        os.makedirs(path)
    return path

def save(path):
    serial = os.environ['ANDROID_SERIAL'] if os.environ.has_key('ANDROID_SERIAL') else None
    #snapshot & system log
    if serial:
        shell('adb -s %s shell screencap /sdcard/laststep.png' % serial)
        shell('adb -s %s pull /sdcard/laststep.png %s' % (serial, path))
        shell('adb -s %s logcat -v time -d > %s ' % (serial, join(path,'log.txt')))
    else:
        shell('adb shell screencap /sdcard/whenfailure.png')
        shell('adb pull /sdcard/whenfailure.png %s' % path)
        shell('adb logcat -v time -d > %s ' % join(path,'log.txt'))


def getServerConfiguration(config):
    ret = {}
    cf = ConfigParser()
    cf.read(config)
    ret.update({'username': cf.get('account', 'username'),\
                'password': cf.get('account', 'password'),\
                'auth': cf.get('server', 'auth'),\
                'session_create': cf.get('server', 'session_create'),\
                'session_update': cf.get('server', 'session_update'),\
                'case_create': cf.get('server', 'case_create'),\
                'case_update': cf.get('server', 'case_update'),\
                'file_upload': cf.get('server', 'file_upload'),\
               })
    return ret

def getJobId():
    '''
    read jobid from file. if NULL return a uuid.
    '''
    return uuid.uuid1()

def getDeviceId():
    '''
    read jobid from file. if NULL return from ENV or adb
    '''
    device_id = None
    if os.environ.has_key('ANDROID_SERIAL'):
        device_id = os.environ['ANDROID_SERIAL'] 
    else:
        device_id = subprocess.check_output(['adb','get-serialno']).strip()
    return device_id

def getProductName():
    '''
    get product name of device
    '''
    device_id = None
    if os.environ.has_key('ANDROID_SERIAL'):
        device_id = os.environ['ANDROID_SERIAL'] 
    else:
        device_id = subprocess.check_output(['adb','get-serialno']).strip()
    return subprocess.check_output(['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.product']).strip()

def getRevision():
    '''
    get revision of device
    '''
    device_id = None
    if os.environ.has_key('ANDROID_SERIAL'):
        device_id = os.environ['ANDROID_SERIAL'] 
    else:
        device_id = subprocess.check_output(['adb','get-serialno']).strip()
    return subprocess.check_output(['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release']).strip()

class LocalReportPlugin(nose.plugins.Plugin):
    """
    change device report/all/fail/error path
    """
    name = 'local-report'
    #score = 200

    def options(self, parser, env):
        """
        Register commandline options.
        Called to allow plugin to register command line options with the parser. DO NOT return a value from this method unless you want to stop all other plugins from setting their options.        
        """
        super(LocalReportPlugin, self).options(parser, env)
        parser.add_option('--remote', action='store_true',
                          dest='remote', default=False,
                          help="upload result to server")

        parser.add_option('--server-config', action='store',  metavar="FILE",
                          dest='server_config', default='server.config',
                          help="specify the server config file")

        parser.add_option('--job-id', action='store', type='string', metavar="STRING",
                          dest='job_id',default=getJobId(),
                          help="the unique id of remote server")

    def configure(self, options, conf):
        """
        Called after the command  line has been parsed, with the parsed options and the config container. Here, implement any config storage or changes to state or operation that are set by command line options. DO NOT return a value from this method unless you want to stop all other plugins from being configured.
        """
        super(LocalReportPlugin, self).configure(options, conf)
        #print '%s:%s' % (TAG, 'plugin config')
        if not self.enabled:
            return
        self.conf = conf
        self.opt = options
        self.session_id = options.job_id

        if options.remote:
            #TODO
            #self.token = None
            server_need = {'username':None, 'password':None, 'auth':None,'session_create':None,
                           'session_update':None, 'case_create':None, 'case_update':None, 'file_upload':None}
            server_configuration = getServerConfiguration(options.server_config)
            sys.stderr.write('*******server configuration********\n')
            sys.stderr.write(str(server_configuration)+'\n')
            self.client =  ReportClient(**server_configuration)
            active = self.client.regist()
            if not active:
                raise Exception('unable to get token from server!')
        ########sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>uuid in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
        ########sys.stderr.write(str(id(conf)))

    #local result
    def begin(self):
        '''
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

        self.test_start_time = _time()
        self.conf.update({'test_start_time':self.test_start_time})
        self._report_path = _mkdir(join(join(os.getcwd(), 'report'), self.test_start_time))
        self._all_report_path = _mkdir(join(self._report_path, 'all'))
        self._fail_report_path = _mkdir(join(self._report_path, 'fail'))
        self._error_report_path = _mkdir(join(self._report_path, 'error'))
        self._timeout_report_path = _mkdir(join(self._report_path, 'timeout'))
        self.tid = 0
        if self.opt.remote:
            session_properties = {'product': 'p',\
                                  'revision': 'r',\
                                  'deviceid': 'devid',\
                                  'planname': 'test.plan',\
                                  'starttime': self.conf.test_start_time
                                 }
            ###client.createSession(**session_properties)

    #local result
    def handleFailure(self, test, err):
        '''
        Called on addFailure. To handle the failure yourself and prevent normal failure processing, return a true value.
        '''
        ############sys.stderr.write(TAG + ' handle failure begin\n')
        #ec, ev, tb = err
        exctype, value, tb = err
        ############sys.stderr.write(str(value)+'\n')
        ############sys.stderr.write(str(exctype)+'\n')
        ############sys.stderr.write(str(tb)+'\n')
        if hasattr(value, 'current') and hasattr(value, 'expect'):
            current = getattr(value, 'current')
            expect = getattr(value, 'expect')
            name, ext = os.path.splitext(os.path.basename(current))
            dest = os.path.dirname(current)
            shutil.copyfile(expect, join(dest, '%s%s%s' % (name, '_expect', ext)))
            save(dest)
            shutil.move(dest, self._fail_report_path)
        else:
            case_start_time = getattr(self.conf, 'case_start_time', None)
            #if not case_start_time:

            class_name = test.id().split('.')[-3]
            case_name = '%s.%s' % (test.id().split('.')[-2], test.id().split('.')[-1])
            tmp = join(os.getcwd(),'tmp')
            case_report_dir = _mkdir(join(tmp, '%s%s%s' % (case_name, '@', self.conf.case_start_time)))
            #last step snapshot
            save(case_report_dir)
            shutil.move(case_report_dir, self._fail_report_path)             
        ######sys.stderr.write(TAG + ' handle failure end\n')


    #local result
    def handleError(self, test, err):
        '''
        Called on addError. To handle the failure yourself and prevent normal error processing, return a true value.
        '''
        sys.stderr.write(TAG + ' handle error begin\n')
        exctype, value, tb = err
        sys.stderr.write(str(value)+'\n')
        sys.stderr.write(str(exctype)+'\n')
        sys.stderr.write(str(tb)+'\n')
        sys.stderr.write(TAG + ' handle error end\n')

##############remote##############
    #remote upload
    def startTest(self, test):
        #if enable remote
        if not self.opt.remote:
            return
        sys.stderr.write(TAG + ' start test in report plugin\n')
        case_start_time = getattr(self.conf, 'case_start_time', None)
        if not case_start_time:
            case_start_time = _time()
            self.conf.update({'case_start_time': case_start_time})

        self.tid += 1
        #report >>> createTest
        domain = test.id().split('.')[-3]
        case_name = '%s%s%s' % (test.id().split('.')[-2], '.', test.id().split('.')[-1])
        sys.stderr.write(TAG + ' start test case request property:\n')
        sys.stderr.write('domain: ' +   domain + '\n')
        sys.stderr.write('casename: ' +  test.id().split('.')[-1] + '\n')
        sys.stderr.write('start time: ' +   self.conf.case_start_time + '\n')
        case_properties = {}
        case_properties.update({'casename':'%s%s%s' % (domain, '.', case_name), 'starttime':self.conf.case_start_time})
        #  {'casename':'%s.%s' % (domain,caseName),'starttime':startTime}
        ###self.client.createCase(**case_properties)

    #remote upload
    def addFailure(self, test, err, capt=None, tbinfo=None):
        if not self.opt.remote:
            return
        sys.stderr.write(TAG + ' add failure in report plugin\n')
        sys.stderr.write(str(self.tid) + 'update fail case result , snapshots, log OKAY \n')

        class_name = test.id().split('.')[-3]
        case_name = '%s%s%s' % (test.id().split('.')[-2], '.', test.id().split('.')[-1])

        tmp = join(os.getcwd(),'tmp')
        case_report_dir = join(tmp, '%s%s%s' % (case_name, '@', self.conf.case_start_time))
        if case_report_dir:
            sys.stderr.write(TAG + 'fail report dir:\n')
            sys.stderr.write(case_report_dir+'\n')
            result_properties = {}
            result_properties.update({'result':'fail', 'time': _time(), 'traceinfo':'empty'})
            ###self.client.updateCase(**result_properties)

    #remote upload
    def addError(self, test, err, capt=None):
        if not self.opt.remote:
            return
        sys.stderr.write(TAG + ' add error in report plugin\n')
        sys.stderr.write(str(self.tid) + 'update error case result , snapshots, log OKAY \n')

        class_name = test.id().split('.')[-3]
        case_name = '%s%s%s' % (test.id().split('.')[-2], '.', test.id().split('.')[-1])
        tmp = join(os.getcwd(),'tmp')

        case_report_dir = join(tmp, '%s%s%s' % (case_name, '@', self.conf.case_start_time))

        if case_report_dir:
            sys.stderr.write(TAG + 'error case report dir:\n')
            sys.stderr.write(case_report_dir+'\n') 
            result_properties = {}
            result_properties.update({'result':'error', 'time': _time(), 'traceinfo':'empty'})
            ###self.client.updateCase(**result_properties)

    #remote upload
    def addSuccess(self, test, capt=None):
        if not self.opt.remote:
            return
        sys.stderr.write(TAG + ' add success in report plugin\n')
        sys.stderr.write(str(self.tid) + 'update success case result , snapshots, log OKAY \n')
        result_properties = {}
        result_properties.update({'result':'pass', 'time': _time(), 'traceinfo':'N/A'})
        ###self.client.updateCase(**result_properties)