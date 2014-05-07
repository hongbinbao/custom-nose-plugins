#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import time
import nose
import json
import shutil
import logging
import datetime
import traceback
from tools import AdbCommand
from os.path import join, exists
from StringIO import StringIO as p_StringO
from cStringIO import OutputType as c_StringO
from uiautomatorplug.android import device, ExpectException


log = logging.getLogger(__name__)

'''global log instance'''
TAG='%s%s%s' % ('-' * 18, 'file output save Plugin', '-' * 18)
'''global log output tag'''
TIME_STAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
'''global time stamp format'''
OUTPUT_FILE_NAME = 'result.txt'
'''global test result output file name'''
LOG_FILE_NAME = 'log.txt'
'''global test log output name'''
FAILURE_SNAPSHOT_NAME = 'failure.png'
'''default string name of result file. can be modify by user-specify'''
#WORDINGDIR = os.environ['WORKSPACE'],
'''default output workspace'''
#SIZE_OF_FILE = 4096
'''default size of result file'''

def _isExecutable(exe):
    '''
    return True if program is executable.
    '''
    return os.path.isfile(exe) and os.access(exe, os.X_OK)

def _findExetuable(program):
    '''
    return the absolute path of executable program if the program available.
    else raise Exception.
    '''
    program_path, program_name = os.path.split(program)
    if program_path:
        if _isExecutable(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if _isExecutable(exe_file):
                return exe_file
    raise Exception(LOCATION_NOT_FOUND_EXCEPTION % program)

def _time():
    '''
    time stamp format
    '''
    #return time.strftime(TIME_STAMP_FORMAT, time.localtime(time.time()))
    return str(datetime.datetime.now())

def _mkdir(path):
    '''
    create directory as path
    '''
    if not exists(path):
        os.makedirs(path)
    return path

def _save(path):
    '''
    pull log from device to report folder
    '''
    serial = os.environ['ANDROID_SERIAL'] if os.environ.has_key('ANDROID_SERIAL') else None
    #snapshot & system log
    bridge = _findExetuable('adb')
    if serial:
        AdbCommand('%s -s %s shell screencap /sdcard/%s' % (bridge ,serial, FAILURE_SNAPSHOT_NAME)).run()
        AdbCommand('%s -s %s pull /sdcard/%s %s' % (bridge, serial, FAILURE_SNAPSHOT_NAME, path)).run()
        output = AdbCommand('%s -s %s logcat -v time -d' % (bridge, serial)).run()
        with open(join(path, LOG_FILE_NAME), 'w') as o:
            o.write(output)
    else:
        AdbCommand('%s shell screencap /sdcard/%s' % (bridge, FAILURE_SNAPSHOT_NAME)).run()
        AdbCommand('%s pull /sdcard/%s %s' % (bridge, FAILURE_SNAPSHOT_NAME, path)).run()
        output = AdbCommand('%s logcat -v time -d ' % bridge).run()
        with open(join(path, LOG_FILE_NAME), 'w') as o:
            o.write(output)

def _writeResultToFile(output, content):
    with open(output, 'a') as f:
        f.write('%s%s' % (json.dumps(content), os.linesep))

def _calcScore(frame):
    """Calculates a score for this stack frame, so that can be used as a
    quality indicator to compare to other stack frames in selecting the
    most developer-friendly one to show in one-line output.

    """
    fname, _, funname, _ = frame
    score = 0.0
    max_score = 7.0  # update this when new conditions are added

    # Being in the project directory means it's one of our own files
    if fname.startswith(os.getcwd()):
        score += 4

    # Being one of our tests means it's a better match
    if os.path.basename(fname).find('test') >= 0:
        score += 2

    # The check for the `assert' prefix allows the user to extend
    # unittest.TestCase with custom assert-methods, while
    # machineout still returns the most useful error line number.
    if not funname.startswith('assert'):
        score += 1
    return score / max_score

def _selectBestStackFrame(traceback):
    best_score = 0
    best = traceback[-1]  # fallback value
    for frame in traceback:
        curr_score = _calcScore(frame)
        if curr_score > best_score:
            best = frame
            best_score = curr_score
            # Terminate the walk as soon as possible
            if best_score >= 1:
                break
    return best


def _formatOutputBrief(name, etype, err):
    exctype, value, tb = err
    fulltb = traceback.extract_tb(tb)
    fname, lineno, funname, msg = _selectBestStackFrame(fulltb)

    #lines = traceback.format _exception_only(exctype, value)
    #lines = [line.strip('\n') for line in lines]
    #msg = lines[0]

    #fname = _format_testfname(fname)
    fname = name
    prefix = "%s:%d" % (fname, lineno)
    return "%s: %s: %s" % (prefix, etype, msg)


def _formatOutput(name, etype, err):
    exception_text = traceback.format_exception(*err)
    #exception_text = "".join(exception_text).replace(os.linesep, '')
    return exception_text

def _splitAll(path):
    """
    Split a path into all of its parts.
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def _relativePath(fromdir, tofile):
    """
    Find relative path from 'fromdir' to 'tofile'.
    An absolute path is returned if 'fromdir' and 'tofile'
    are on different drives.
    """
    if not tofile:
        return tofile
    f1name = os.path.abspath(tofile)
    if os.path.splitdrive(f1name)[0]:
        hasdrive = True
    else:
        hasdrive = False
    f1basename = os.path.basename(tofile)
    f1dirname = os.path.dirname(f1name)
    f2dirname = os.path.abspath(fromdir)
    f1parts = _splitAll(f1dirname)
    f2parts = _splitAll(f2dirname)
    if hasdrive and (f1parts[0].lower() <> f2parts[0].lower()):
        "Return absolute path since we are on different drives."
        return f1name
    while f1parts and f2parts:
        if hasdrive:
            if f1parts[0].lower() <> f2parts[0].lower():
                break
        else:
            if f1parts[0] <> f2parts[0]:
                break
        del f1parts[0]
        del f2parts[0]
    result = ['..' for part in f2parts]
    result.extend(f1parts)
    result.append(f1basename)
    return os.sep.join(result)

class FileOutputPlugin(nose.plugins.Plugin):
    """
    write test result to $WORKSPACE/result.txt or ./result.txt
    """
    name = 'file-output'

    def options(self, parser, env):
        """
        Register commandline options.
        Called to allow plugin to register command line options with the parser. DO NOT return a value from this method unless you want to stop all other plugins from setting their options.        
        """
        super(FileOutputPlugin, self).options(parser, env)

        parser.add_option('--output-file-name', 
                          dest='file_name', default='result.txt',
                          help="save output file to this directory")

        parser.add_option('--output-directory', action='store_true',
                          dest='directory', default=self.__getDefault(),
                          help="save output file to this directory")

    def __getDefault(self):
        workspace = os.getcwd()
        if 'WORKSPACE' in os.environ:
            ws = os.environ['WORKSPACE']
            workspace = _mkdir(ws)
        return workspace

    def configure(self, options, conf):
        """
        Called after the command  line has been parsed, with the parsed options and the config container. Here, implement any config storage or changes to state or operation that are set by command line options. DO NOT return a value from this method unless you want to stop all other plugins from being configured.
        """
        super(FileOutputPlugin, self).configure(options, conf)
        if not self.enabled:
            return
        self.write_hashes = conf.verbosity == 2
        self.conf = conf
        self.opt = options
        self.result_file = join(_mkdir(self.opt.directory), self.opt.file_name)
        #assert exists(self.result_file), 'file not found!'
        self.result_properties = {}

    def begin(self):
        self.test_start_time = getattr(self.conf, 'test_start_time', None)
        if not self.test_start_time:
            self.test_start_time = datetime.datetime.now()
            self.conf.update({'test_start_time': str(self.test_start_time)})
        
        self._report_path = _mkdir(join(join(self.opt.directory, 'report'), str(self.test_start_time).replace(' ', '_')))
        self._all_report_path = _mkdir(join(self._report_path, 'all'))
        self._fail_report_path = _mkdir(join(self._report_path, 'fail'))
        self._error_report_path = _mkdir(join(self._report_path, 'error'))
        self._timeout_report_path = _mkdir(join(self._report_path, 'timeout'))

    def beforeTest(self, test):
        case_start_time = getattr(self.conf, 'case_start_time', None)
        if not case_start_time:
            case_start_time = datetime.datetime.now()
            self.conf.update({'case_start_time': case_start_time})

        ######sys.stderr.write(case_start_time+'\n')
        #test case local output pakcage
        module_name, class_name, method_name = test.id().split('.')[-3:]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)
        
        device.right_dir_path = join(join(join(os.getcwd(), test.id().split('.')[0]), 'pics'), '%s%s%s'%(module_name, '.', case_dir_name))
        
        tmp = join(os.getcwd(), 'tmp')
        case_report_dir = _mkdir(join(tmp, '%s%s%s' % (case_dir_name, '@', str(self.conf.case_start_time).replace(' ', '_'))))
        device.report_dir_path = case_report_dir

    def startTest(self, test):
        """
        startTest: called after beforeTest(*)
        """
        case_start_time = getattr(self.conf, 'case_start_time', None)
        if not case_start_time:
            case_start_time = datetime.datetime.now()
            self.conf.update({'case_start_time': case_start_time})
        if self.write_hashes:
            sys.stderr.write('%s%s' % (str(case_start_time), ' '))

    def stopTest(self, test):
        """
        stopTest: called before afterTest(*)
        """
        pass

    def afterTest(self, test):
        self.conf.update({'case_start_time': None})
        device.report_dir_path = None
        device.right_dir_path = None

    def handleFailure(self, test, err):
        '''
        Called on addFailure. To handle the failure yourself and prevent normal failure processing, return a true value.
        '''
        #sys.stderr.write(TAG + ' handle failure begin\n')
        self.result_properties.clear()
        exctype, value, tb = err

        module_name = test.id().split('.')[-3]
        class_name = test.id().split('.')[-2]
        method_name = test.id().split('.')[-1]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)
        case_start_time = self.conf.case_start_time
        case_report_dir_name = '%s%s%s' % (case_dir_name, '@', str(case_start_time).replace(' ', '_'))
        case_report_dir_path = join(self._fail_report_path, case_report_dir_name)
        screenshot_at_failure = None
        log = None
        expect = None

        if hasattr(value, 'current') and hasattr(value, 'expect'):
            current = getattr(value, 'current')
            expect = getattr(value, 'expect')
            snapshot_name = os.path.basename(current)
            name, ext = os.path.splitext(snapshot_name)
            dest = os.path.dirname(current)
            expect_snapshot_name = '%s%s%s' % (name, '_expect', ext)
            shutil.copyfile(expect, join(dest, expect_snapshot_name))
            _save(dest)
            shutil.move(dest, self._fail_report_path)
            #"screenshot_at_failure"
            screenshot_at_failure = join(case_report_dir_path, snapshot_name)
            log = join(case_report_dir_path, LOG_FILE_NAME)
            expect = join(case_report_dir_path, expect_snapshot_name)
            
        else:

            tmp = join(os.getcwd(), 'tmp')
            case_report_dir = _mkdir(join(tmp, case_report_dir_name))
            #last step snapshot
            _save(case_report_dir)
            shutil.move(case_report_dir, self._fail_report_path)

            screenshot_at_failure = join(case_report_dir_path, FAILURE_SNAPSHOT_NAME)
            log = join(case_report_dir_path, LOG_FILE_NAME)
            expect = None

        self.result_properties.update({'screenshot_at_failure': _relativePath(self.opt.directory, screenshot_at_failure),
                                       'log': _relativePath(self.opt.directory, log),
                                       'expect': _relativePath(self.opt.directory, expect)
                                       })

    def handleError(self, test, err):
        '''
        Called on addError. To handle the failure yourself and prevent normal error processing, return a true value.
        '''
        self.result_properties.clear()
        exctype, value, tb = err
        module_name = test.id().split('.')[-3]
        class_name = test.id().split('.')[-2]
        method_name = test.id().split('.')[-1]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)
        case_start_time = self.conf.case_start_time
        case_report_dir_name = '%s%s%s' % (case_dir_name, '@', str(case_start_time).replace(' ', '_'))
        case_report_dir_path = join(self._error_report_path, case_report_dir_name)

        screenshot_at_failure = None
        log = None
        expect = None

        if hasattr(value, 'current') and hasattr(value, 'expect'):
            current = getattr(value, 'current')
            expect = getattr(value, 'expect')
            snapshot_name = os.path.basename(current)
            name, ext = os.path.splitext(snapshot_name)
            dest = os.path.dirname(current)
            expect_snapshot_name = '%s%s%s' % (name, '_expect', ext)
            shutil.copyfile(expect, join(dest, expect_snapshot_name))
            _save(dest)
            shutil.move(dest, self._error_report_path)
            #"screenshot_at_failure"
            screenshot_at_failure = join(case_report_dir_path, snapshot_name)
            log = join(case_report_dir_path, LOG_FILE_NAME)
            expect = join(case_report_dir_path, expect_snapshot_name)
            
        else:

            tmp = join(os.getcwd(), 'tmp')
            case_report_dir = _mkdir(join(tmp, case_report_dir_name))
            #last step snapshot
            _save(case_report_dir)
            shutil.move(case_report_dir, self._error_report_path)

            screenshot_at_failure = join(case_report_dir_path, FAILURE_SNAPSHOT_NAME)
            log = join(case_report_dir_path, LOG_FILE_NAME)
            expect = None

        self.result_properties.update({'screenshot_at_failure': _relativePath(self.opt.directory, screenshot_at_failure),
                                       'log': _relativePath(self.opt.directory, log),
                                       'expect': _relativePath(self.opt.directory, expect)
                                       })

    def addFailure(self, test, err, capt=None, tbinfo=None):
        #sys.stderr.write(TAG + ' add failure in fileoutput plugin\n')
        #sys.stderr.write('addFailure>>>>>>'*100+'\n')

        module_name = test.id().split('.')[-3]
        class_name = test.id().split('.')[-2]
        method_name = test.id().split('.')[-1]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)
        case_start_time = self.conf.case_start_time
       

        self.result_properties.update({'start_at': str(case_start_time),
                                      'name': case_dir_name,
                                      'result': 'fail',
                                      'end_at': str(datetime.datetime.now()),
                                      'trace':_formatOutput(case_dir_name, 'fail', err)
                                      })
            
        _writeResultToFile(self.result_file, self.result_properties)


    #remote upload
    def addError(self, test, err, capt=None):
        #sys.stderr.write(TAG + ' add error in report plugin\n')

        module_name = test.id().split('.')[-3]
        class_name = test.id().split('.')[-2]
        method_name = test.id().split('.')[-1]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)
        case_start_time = self.conf.case_start_time

        self.result_properties.update({'start_at': str(case_start_time),
                                      'name': case_dir_name, 
                                      'result': 'error',
                                      'end_at': str(datetime.datetime.now()),
                                      'trace':_formatOutput(case_dir_name, 'error', err)
                                      })
        _writeResultToFile(self.result_file, self.result_properties)

    #remote upload
    def addSuccess(self, test, capt=None):
        #sys.stderr.write(TAG + ' add success in report plugin\n')

        module_name = test.id().split('.')[-3]
        class_name = test.id().split('.')[-2]
        method_name = test.id().split('.')[-1]
        case_dir_name = '%s%s%s' % (class_name, '.', method_name)

        self.result_properties.clear()
        self.result_properties.update({'name':case_dir_name, 'result':'pass', 'start_at':str(self.conf.case_start_time), 'end_at': str(datetime.datetime.now())})
        _writeResultToFile(self.result_file, self.result_properties)
