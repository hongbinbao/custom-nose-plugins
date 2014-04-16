#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import logging
import ConfigParser
from collections import  OrderedDict
import nose
import unittest
from nose.loader import defaultTestLoader
from inspect import getmodule
log = logging.getLogger(__name__)
from nose.suite import *

class CustomTestLoader(nose.loader.TestLoader):
    def __init__(self, plan, section, loop):
        self._plan = plan
        self._section = section
        self._loop = loop

    def getTestsFromFile(self, plan_file_path, section_name, loop):
        tests = []
        parser = ConfigParser.ConfigParser(dict_type=OrderedDict)
        parser.optionxform = lambda x: x
        parser.read(plan_file_path)
        tests = parser.items(section_name)
        n = 1
        while n <= int(loop): 
            for (k,v) in tests:
                for i in range(int(v)):
                    yield k
            n += 1

    def loadTestsFromNames(self, names, module=None):
        """Override to load tests from a file which specify each test case order and loop. the file format:
        [tests]
        packagename.modulename.classname.testName = 10
        packagename.modulename.classname.testName = 20
        """
        names = self.getTestsFromFile(self._plan, self._section, self._loop)
        def yielder():
            for i in names:
                yield unittest.TestLoader().loadTestsFromName(i)
        #<unittest.suite.TestSuite tests=[<scripts.testcases.browser.BrowserTest testMethod=testOpenBrowser>]>
        tests = []
        #for i in yielder():
        #    tests.append(i)
        return nose.suite.ContextSuiteFactory()(yielder())

class PlanLoaderPlugin(nose.plugins.Plugin):
    """
    test loader plugin. allow to specify a test plan file with format:
    [tests]
    packagename.modulename.classname.testName = 10
    packagename.modulename.classname.testName = 20 
    """
    name = 'plan-loader'
    planfile = None
    score = 100

    def options(self, parser, env):
        """Register commandline options.
        """
        super(PlanLoaderPlugin, self).options(parser, env)
        #parser.add_option('--stability-test-loader', action='store_true',
        #                  dest='stability_test_loader', default=False,
        #                  help="enable stability test loader plugin")

        parser.add_option('--plan-file-name', action='store', type='string',metavar="STRING",
                          dest='plan_file', default='plan',
                          help="Run the tests that list in plan file")

        parser.add_option('--plan-loop-number', action='store', type='string',metavar="STRING",
                          dest='loops', default='1',
                          help="Run the tests with specified loop number. default will execute forever ")


    def configure(self, options, conf):
        """Configure plugin.
        """
        super(PlanLoaderPlugin, self).configure(options, conf)
        if not self.enabled:
            return
        #print options
        #if options.stability_test_loader:
        #    self.enabled = True
        self.conf = conf
        if options.plan_file:
            self.enabled = True
        if options.loops:
            self.enabled = True
            self.loops = options.loops
        self.plan_file = os.path.expanduser(options.plan_file)
        if not os.path.isabs(self.plan_file):
            self.plan_file = os.path.join(conf.workingDir, self.plan_file)
        if not os.path.exists(self.plan_file):
            raise Exception('file not found: %s' % self.plan_file)

    def prepareTestLoader(self, loader):
        """
        Get handle on test loader so we can use it in loadTestsFromNames.
        """
        self.loader = loader
        self.suiteClass = loader.suiteClass

    def getTestsFromPlanFile(self, plan_file_path, section_name, loop):
        tests = []
        parser = ConfigParser.ConfigParser(dict_type=OrderedDict)
        parser.optionxform = lambda x: x
        parser.read(plan_file_path)
        tests = parser.items(section_name)
        n = 1
        while n <= int(loop): 
            for (k,v) in tests:
                for i in range(int(v)):
                    yield k
            n += 1

    def loadTestsFromNames2(self, names, module=None):
        """
        replace the way of loading test case using plan file.
        if return lazy zuite. the wrapped method provided by nose will be not work
        """
        loader = self.loader
        names = self.getTestsFromPlanFile(plan_file_path=self.plan_file, section_name='tests', loop=self.loops)
        #names = ['scripts.testcases.phone:Phone.testCall', 'scripts.testcases.browser:Browser.testOpenBrowser', 'scripts.testcases.phone:Phone.testCall']
        #tests = []
        def lazy():
            for name in names:
                yield unittest.TestLoader().loadTestsFromName(name, module)
                #yield loader.loadTestsFromName(name, module)
                #tests.append(unittest.TestLoader().loadTestsFromName(name, module))
        #for name in names:
        #    tests.append(unittest.TestLoader().loadTestsFromName(name, module))
        #return (ContextList(tests), [])
        #return (ContextSuite(lazy), [])
        return (loader.suiteClass(lazy), [])
        #return (None, lazy())

    def loadTestsFromNames(self, names, module=None):
        """
        replace the way of loading test case using plan file.
        """
        loader = self.loader
        names = self.getTestsFromPlanFile(plan_file_path=self.plan_file, section_name='tests', loop=self.loops)
        return (None, names)


    def loadTestsFromName(self, name, module=None, discovered=False):
        #unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)
        return unittest.TestLoader().loadTestsFromName(name, getmodule(name))

    def wantModule(self,module):
        return False

    def wantMethod(self,method):
        return True
