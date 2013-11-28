#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import time
import logging
import shutil
import tempfile
import threading
from ConfigParser import ConfigParser
import nose
from commands import getoutput as shell
from os.path import join, exists
import io
from PIL import Image
import requests
import math
log = logging.getLogger(__name__)


TAG='----------------------***********ScreenMonitorPlugin*************-----------------------'
REFRESH_TIME = 2
SNAPSHOT_NAME = 'sc.png'
#########jobid | deviceid | scaled snapshot

MAXIMUM_RETRY_COUNT = 2
def retry(tries, delay=1, backoff=2):
  '''
  retries a function or method until it returns True.
  delay sets the initial delay, and backoff sets how much the delay should
  lengthen after each failure. backoff must be greater than 1, or else it
  isn't really a backoff. tries must be at least 0, and delay greater than
  0.
  '''

  if backoff <= 1: 
    raise ValueError("backoff must be greater than 1")
  tries = math.floor(tries)
  if tries < 0: 
    raise ValueError("tries must be 0 or greater")
  if delay <= 0: 
    raise ValueError("delay must be greater than 0")
  def deco_retry(f):
    def f_retry(*args, **kwargs):
      mtries, mdelay = tries, delay # make mutable
      rv = f(*args, **kwargs) # first attempt
      while mtries > 0:
        if rv != None or type(rv) == str or type(rv) == dict: # Done on success ..
          return rv
        mtries -= 1      # consume an attempt
        time.sleep(mdelay) # wait...
        mdelay *= backoff  # make future wait longer
        rv = f(*args, **kwargs) # Try again
      #print 'retry %d times all failed. plese check server status' % tries
      #sys.exit(1)
      return False # Ran out of tries
    return f_retry # true decorator -> decorated function
  return deco_retry  # @retry(arg[, ...]) -> true decorator

@retry(MAXIMUM_RETRY_COUNT)
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
        #sys.stderr.write('>>>>>>>>>>>>>>>>begin to send request>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        ret = req(url=url, data=data, **kwargs).json()
        #sys.stderr.write('>>>>>>>>>>>>>>>>>over to send request>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        if ret and 'errors' in ret.keys():
            raise Exception(dict(ret))
    except requests.exceptions.Timeout, e:
        print e
    except requests.exceptions.TooManyRedirects:
        print e
    except requests.exceptions.RequestException as e:
        print e
    except Exception, e:
        print e
    return ret

class MonitorThread(threading.Thread):
    '''
    used to send snapshots data to widget(adb ,sdb bridge)
    '''

    def __init__(self, **kwargs):
        super(MonitorThread, self).__init__()
        self.daemon = True
        self.isStop = False
        self.bridge = kwargs['bridge']
        self.path = kwargs['temppath']
        self.url = kwargs['url']

    def run(self):
        if self.bridge == 'sdb':
            cmd = 'sdb shell gst-launch-0.10 ximagesrc num-buffers=1 ! ffmpegcolorspace ! pngenc ! filesink location=sc.png'
            pullcmd = '%s %s %s %s%s%s' % ('sdb', 'pull', 'sc.png', '.', os.sep, SNAPSHOT_NAME )
        elif self.bridge =='adb':
            cmd = 'adb shell screencap /sdcard/sc.png'
            pullcmd = '%s %s %s %s' % ('adb', 'pull', '/sdcard/sc.png', os.path.join(self.path, SNAPSHOT_NAME))
        elif self.bridge == 'ssh':
            cmd = ''
            pullcmd = ''
        while not self.isStop:
            shell(cmd)
            shell(pullcmd)
            if exists(join(self.path, SNAPSHOT_NAME)):
                image = Image.open(join(self.path, SNAPSHOT_NAME))
                image.thumbnail((100,200))
                files = {'file': image.tostring()}
                values = {'token':'', 'jobid':''}
                request(method='post', url=self.url, files=files, data=values, timeout=5)

    def stop(self):
        self.isStop = True

class ScreenMonitorPlugin(nose.plugins.Plugin):
    """
    uploading scaled screen to server
    """
    score = 100 #after dut-configer 100
    name = 'screen-monitor'

    def options(self, parser, env):
        """
        Register commandline options.
        Called to allow plugin to register command line options with the parser. DO NOT return a value from this method unless you want to stop all other plugins from setting their options.        
        """
        super(ScreenMonitorPlugin, self).options(parser, env)
        log.debug('%s:%s' % (TAG, 'options init'))
        parser.add_option('--device-id', action='store', type='string', metavar="STRING",
                          dest='device_id', default='',
                          help="specify the id of device")

        parser.add_option('--job-id', action='store', type='string', metavar="STRING",
                          dest='job_id',default=self.__getJobId(),
                          help="the unique id of remote server")

        parser.add_option('--server-config', action='store', type='string', metavar="STRING",
                          dest='server_config', default='server.config',
                          help="url of remote server")

        parser.add_option('--tmp-path', action='store', type='string', metavar="STRING",
                          dest='tmp_path', default='',
                          help="path of the snapshot saving directory")

        parser.add_option('--save', action='store_true',
                          dest='save', default=False,
                          help="path of the snapshot saving directory")

    def configure(self, options, conf):
        """
        Called after the command line has been parsed, with the parsed options and the config container. Here, implement any config storage or changes to state or operation that are set by command line options. DO NOT return a value from this method unless you want to stop all other plugins from being configured.
        """
        super(ScreenMonitorPlugin, self).configure(options, conf)
        #print '%s:%s' % (TAG, 'plugin config')
        if not options.job_id:
            raise Exception('no job id')
        self.job_id = options.job_id
        self.tmp_path = tempfile.mkdtemp() if not options.tmp_path else options.tmp_path
        if options.server_config:
            self.server_config = options.server_config
            if os.path.exists(self.server_config):
                self.url = self.__loadConfig(self.server_config) % self.job_id 
            else: raise Exception('server config file not found: %s' % self.server_config)
        self.save = options.save
        args = {'bridge':'adb', 'temppath':self.tmp_path, 'url': self.url }
        self.monitor = MonitorThread(**args)

    def __getJobId(self):
            return '1111'

    def __loadConfig(self, config):
        '''
        read server API from server.config file
        '''
        cf = ConfigParser()
        cf.read(config)
        return cf.get('server','url')

    def prepareTest(self, test):
        '''
        Only once. Called before the test is run by the test runner. after test was collected
        '''
        #sys.stderr.write('pppppppppppppppppppppppppppppppppp in screenmonitor'+'\n')
        #add test start time stamp for whole test session
        #configer.update({'test_start_time': _time()})
        pass

    def begin(self):
        '''
        Only once. Called before any tests are collected(not collected yet) or run. Use this to perform any setup needed before testing  begins.
        '''
        #start uploading thread
        self.monitor.start()

    def finalize(self, result):
        #sys.stderr.write(str(result) + '\n')
        try:
            self.monitor.stop()
            if not self.save:
                shutil.rmtree(self.tmp_path)
        except:
            pass
