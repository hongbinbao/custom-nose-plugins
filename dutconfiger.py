#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import time
import logging
import shutil
import nose
from commands import getoutput as shell
from devicewrapper.config import configer
from os.path import join, exists
log = logging.getLogger(__name__)


TIME_STAMP_FORMAT = '%Y-%m-%d_%H:%M:%S'
TAG='----------------------**********DUTConfigerPlugin**************-----------------------'

def _time():
    return time.strftime(TIME_STAMP_FORMAT, time.localtime(time.time()))

def _mkdir(path):
    if not exists(path):
        os.makedirs(path)
    return path

def handle():
    serial = configer.env['ANDROID_SERIAL'] if configer.env.has_key('ANDROID_SERIAL') else None
    #snapshot & system log
    if serial:
        shell('adb -s %s shell screencap /sdcard/whenfailure.png' % serial)
        shell('adb -s %s pull /sdcard/whenfailure.png %s' % (serial, configer['report_dir_path']))
        shell('adb -s %s logcat -v time -d > %s ' % (serial,os.path.join(configer['report_dir_path'],'log.txt')))
    else:
        shell('adb shell screencap /sdcard/whenfailure.png')
        shell('adb pull /sdcard/whenfailure.png %s' % configer['report_dir_path'])
        shell('adb logcat -v time -d > %s ' % os.path.join(configer['report_dir_path'],'log.txt'))

class DUTConfigerPlugin(nose.plugins.Plugin):
    """
    change device report/all/fail/error path
    """
    name = 'dut-configer'
    score = 200

    def options(self, parser, env):
        """
        Register commandline options.
        Called to allow plugin to register command line options with the parser. DO NOT return a value from this method unless you want to stop all other plugins from setting their options.        
        """
        super(DUTConfigerPlugin, self).options(parser, env)
        #log.debug('%s:%s' % (TAG, 'options init'))
        pass

    def configure(self, options, conf):
        """
        Called after the command line has been parsed, with the parsed options and the config container. Here, implement any config storage or changes to state or operation that are set by command line options. DO NOT return a value from this method unless you want to stop all other plugins from being configured.
        """
        super(DUTConfigerPlugin, self).configure(options, conf)
        #print '%s:%s' % (TAG, 'plugin config')
        pass

    #./report
    #./tescases/message.py
    def startTest(self, test):
        """
        Called before each test is run. DO NOT return a value unless you want to stop other plugins from seeing the test start.
        """

        #sys.stderr.write('%s:%s' % (TAG, 'start test')+'\n')
        #init dir for report and save
        class_name = test.__module__.split('.')[2]
        case_name = '%s.%s' %(type(test).__name__, test._testMethodName)
        method_name = test._testMethodName
        configer['right_dir_path'] = join(join(join(configer['working_dir'], test.__module__.split('.')[0]), 'pics'), '%s.%s'%(class_name, case_name))
        
        #sys.stderr.write(TAG)
        #sys.stderr.write(str(type(test)))
        configer['report_dir_path'] = _mkdir(join(self._all_report_path,'%s@%s' % (case_name, _time())))

    def stopTest(self, test):
        """
        Called after each test is run. DO NOT return a value unless you want to stop other plugins from seeing that the test has stopped.
        """
        #sys.stderr.write(TAG+'-stop test'+'\n')
        #sys.stderr.write(configer['right_dir_path']+'\n')
        #sys.stderr.write(configer['report_dir_path']+'\n')
        pass

    def prepareTest(self, test):
        '''
        Only once. Called before the test is run by the test runner. after test was collected
        '''
        #add test start time stamp for whole test session
        configer.update({'test_start_time': _time()})
        self._report_path = _mkdir(os.path.join(os.path.join(configer['working_dir'], 'report'), configer['test_start_time']))
        self._all_report_path = _mkdir(os.path.join(self._report_path, 'all'))
        self._fail_report_path = _mkdir(os.path.join(self._report_path, 'fail'))
        self._error_report_path = _mkdir(os.path.join(self._report_path, 'error'))
        self._timeout_report_path = _mkdir(os.path.join(self._report_path, 'timeout'))

    def begin(self):
        '''
        Only once. Called before any tests are collected(not collected yet) or run. Use this to perform any setup needed before testing  begins.
        '''
        pass

    def beforeTest(self, test):
        '''
        Before each test case. Called before the test is run (before startTest).
        '''   

    def afterTest(self, test):
        """
        Called after the test has been run and the result recorded (after stopTest).
        """
        #configer.reset()
        pass

    def handleFailure(self, test, err):
        '''
        Called on addFailure. To handle the failure yourself and prevent normal failure processing, return a true value.
        '''
        #sys.stderr.write(TAG+'-handle failure'+'\n')
        #sys.stderr.write(configer['right_dir_path']+'\n')
        #sys.stderr.write(configer['report_dir_path']+'\n')
        handle()
        shutil.move(configer['report_dir_path'], self._fail_report_path)
        

    def handleError(self, test, err):
        '''
        Called on addError. To handle the failure yourself and prevent normal error processing, return a true value.
        '''
        #sys.stderr.write(TAG+'-handle error'+'\n')
        #sys.stderr.write(configer['right_dir_path']+'\n')
        #sys.stderr.write(configer['report_dir_path']+'\n')
        handle()
        shutil.move(configer['report_dir_path'], self._error_report_path)
































