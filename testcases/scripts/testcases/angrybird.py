#!/usr/bin/python
# -*- coding:utf-8 -*- 
import unittest
from devicewrapper.android import device as d

class AngrybirdTest(unittest.TestCase):
    def setUp(self):
        super(AngrybirdTest, self).setUp()
        #d.start_activity(action='android.intent.action.DIAL', data='tel:13581739891', flags=0x04000000)
        d.wakeup()
        d.press('back')
        d.press('back')
        d.press('home')

    def tearDown(self):
        super(AngrybirdTest, self).tearDown()
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def testLaunch(self):
        #assert d.exists(text='Angry Birds') , 'wechat app not appear on the home screen'
        #assert d.exists(text='Apps')  , 'not appear on the home screen'
        #d(text='Angry Birds').click.wait()
        #d.sleep(30)
        d.expect('loaded.png')
        