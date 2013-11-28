#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import sys
import logging
import ConfigParser
from collections import  OrderedDict
import nose
import unittest

class CustomTestLoader(unittest.TestLoader):
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

    def TODOloadTestsFromNames(self, names, module=None):
        """Override to load tests from a file which specify each test case order and loop. the file format:
        [tests]
        packagename.modulename.classname.testName = 10
        packagename.modulename.classname.testName = 20
        """
        names = self.getTestsFromFile(self._plan, self._section, self._loop)
        def yielder():
            for i in names:
                yield unittest.TestLoader().loadTestsFromName(i)
        return nose.suite.ContextSuite(yielder)

log = logging.getLogger(__name__)

class PlanLoaderPlugin(nose.plugins.Plugin):
    """
    test loader plugin. allow to specify a test plan file with format:
    [tests]
    packagename.modulename.classname.testName = 10
    packagename.modulename.classname.testName = 20 
    """
    name = 'plan-loader'
    planfile = None

    def options(self, parser, env):
        """Register commandline options.
        """
        super(PlanLoaderPlugin, self).options(parser, env)
        #parser.add_option('--stability-test-loader', action='store_true',
        #                  dest='stability_test_loader', default=False,
        #                  help="enable stability test loader plugin")

        parser.add_option('--plan-file', action='store', type='string',metavar="STRING",
                          dest='plan_file', default='plan',
                          help="Run the tests that list in plan file")

        parser.add_option('--loop', action='store', type='string',metavar="STRING",
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

    def TODOprepareTestLoader(self, loader):
        """Called before tests are loaded. To replace the test loader,
        return a test loader. To allow other plugins to process the
        test loader, return None. Only one plugin may replace the test
        loader. Only valid when using nose.TestProgram.

        :Parameters:
           loader : :class:`nose.loader.TestLoader` 
             (or other loader instance) the test loader
        """
        loader = CustomTestLoader(plan=self.plan_file, section='tests', loop=self.loops)
        return loader


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

    def loadTestsFromNames(self, names, module=None):
        """
        replace the way of loading test case using plan file.
        """
        log.debug('load----------------------------------------------------------------begin')
        sys.stderr.write('load----------------------------------------------------------------begin')
        ret = self.getTestsFromPlanFile(plan_file_path=self.plan_file, section_name='tests', loop=self.loops)
        log.debug('load----------------------------------------------------------------end')
        sys.stderr.write('load----------------------------------------------------------------end')
        return [None, ret]

    def loadTestsFromName(self, name, module=None, discovered=False):
        log.debug('load tests from name-------------------------------------------------------------')
        sys.stderr.write('load from name----------------------------------------------------------------begin')
        return unittest.TestLoader().loadTestsFromName(name)

