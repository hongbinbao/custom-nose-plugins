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
from client import Authentication
import subprocess

log = logging.getLogger(__name__)

warning = "Cannot access the test config because the plugin has not \
been activated.  Did you specify --with-remote-report or any other command line option?"

config = {}

TIME_STAMP_FORMAT = '%Y-%m-%d_%H:%M:%S'
TAG='----------------------**********RemmoteReportPlugin**************-----------------------'

def _time():
    return time.strftime(TIME_STAMP_FORMAT, time.localtime(time.time()))

def _mkdir(path):
    if not exists(path):
        os.makedirs(path)
    return path

def getContentType(filename):
    '''
    lists and converts supported file extensions to MIME type
    '''
    ext = filename.split('.')[-1].lower()
    if ext == 'png': return 'image/png'
    if ext == 'gif': return 'image/gif'
    if ext == 'svg': return 'image/svg+xml'
    if ext == 'jpg' or ext == 'jpeg': return 'image/jpeg'
    return None

def getSessionConfiguration(config):
    return {'sessioninfo':'urls'}

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

class RemoteReportPlugin(nose.plugins.Plugin):
    """
    change device report/all/fail/error path
    """
    name = 'remote-report'
    #score = 300

    def options(self, parser, env):
        """
        Register commandline options.
        Called to allow plugin to register command line options with the parser. DO NOT return a value from this method unless you want to stop all other plugins from setting their options.        
        """
        super(RemoteReportPlugin, self).options(parser, env)
        #log.debug('%s:%s' % (TAG, 'options init'))
        parser.add_option('--server-config', action='store', type='string', metavar="STRING",
                          dest='server_config', default='server.config',
                          help="specify the server config file")

        parser.add_option('--job-id', action='store', type='string', metavar="STRING",
                          dest='job_id',default=getJobId(),
                          help="the unique id of remote server")

        parser.add_option('--device-id', action='store', type='string', metavar="STRING",
                          dest='device_id',default=getDeviceId(),
                          help="the serial id of device")

    #plugin should only care enable/disable --configfile
    def configure(self, options, conf):
        '''
        Called after the command line has been parsed, with the parsed options and the config container. Here, implement any config storage or changes to state or operation that are set by command line options. DO NOT return a value from this method unless you want to stop all other plugins from being configured.
        '''
        super(RemoteReportPlugin, self).configure(options, conf)
        conf.capture = False
        #if not enable by user > ignore
        if not self.enabled:
            return
        if options.server_config:
            if not os.path.exists(options.server_config):
                raise Exception('server.config not found')
        self.server_need = getSessionConfiguration(options.server_config)

        self.session_id = options.job_id

        #session.update({'starttime':_time(), 'sid':self.session_id})
        #here to validate if the remote server OK. if active failed. raise to abort testing

        req_token = {}
        req_token.update(self.server_need)
        self.token = Authentication.getToken(**req_token)
        if not self.token:
            raise Exception('get token error')

        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>uuid in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
        sys.stderr.write(str(id(conf)))
        #

    def prepareTest(self, test):
        '''
        Only once. Called before any tests are collected(not collected yet) or run. Use this to perform any setup needed before testing  begins.
        '''
        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>begin test in remote plugins>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
        #begin to generate test id from 0
        sid = self.session_id
        product = ''
        revision = ''
        start_time = ''
        plan_name = ''
        device_id = ''

    def startTest(self, test):
        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>start test in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
        sys.stderr.write(device.report_dir_path + '\n')

    def addFailure(self, test, err, capt=None, tbinfo=None):
        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>add failure in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
        sys.stderr.write('>>>what to upload when failure>>>\n')
        sys.stderr.write(device.report_dir_path+'\n')
        #url domain/sid/case/cid/
        pass

    def addError(self, test, err, capt=None):
        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>add error in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        sys.stderr.write('>>>what to upload when error>>>\n')
        sys.stderr.write(device.report_dir_path + '\n')    
        pass

    def addSuccess(self, test, capt=None):
        sys.stderr.write('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>add success in remote plugin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        sys.stderr.write('>>>what to upload when success>>>\n')
        sys.stderr.write('just basic result\n')  
