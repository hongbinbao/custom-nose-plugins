#!/usr/bin/python
# -*- coding:utf-8 -*- 
import unittest
from devicewrapper.android import device as d

class WeiboTest(unittest.TestCase):
    def setUp(self):
        super(WeiboTest, self).setUp()
        #d.start_activity(action='android.intent.action.DIAL', data='tel:13581739891', flags=0x04000000)
        d.wakeup()
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def tearDown(self):
        super(WeiboTest, self).tearDown()
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def testWeibo(self):
        assert d.exists(text='Weibo') , 'wechat app not appear on the home screen'
        #assert d.exists(text='Apps')  , 'not appear on the home screen'
        d(text='Weibo').click.wait()
        assert d(className='android.widget.TextView', description="MainEdit").wait.exists(timeout=10000), 'weibo cient unable to open in 10 secs'
        if d.exists(text='Sent failed. It has been saved in the draft.'):
            d(text='Sent failed. It has been saved in the draft.').click.wait()
            d.press('back')
        d.swipe(350, 420, 350, 820)
        d.sleep(3)
        #d(description="首页列表").click.wait()
        
        d(className='android.widget.TextView', description="MainEdit").click.wait()
        assert d(className='android.widget.TextView', text="New Weibo").wait.exists(timeout=3000), 'unable to compose message'
        d(className='android.widget.EditText').set_text('funny funny bear')
        d(text='Send', description='Send').click.wait()
        assert not d(text='Sent failed. It has been saved in the draft.').wait.exists(timeout=10000), 'msg send failed'
        assert d(className='android.widget.TextView', description="MainEdit").wait.exists(timeout=10000), 'unable to back to home screen in 10 secs'
       