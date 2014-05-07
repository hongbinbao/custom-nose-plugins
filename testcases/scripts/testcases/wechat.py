#!/usr/bin/python
# -*- coding:utf-8 -*- 
import unittest
from devicewrapper.android import device as d

class WechatTest(unittest.TestCase):
    def setUp(self):
        super(WechatTest, self).setUp()
        #d.start_activity(action='android.intent.action.DIAL', data='tel:13581739891', flags=0x04000000)
        d.wakeup()
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def tearDown(self):
        super(WechatTest, self).tearDown()
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def testWechat(self):
        assert d.exists(text='WeChat') , 'wechat app not appear on the home screen'
        #assert d.exists(text='Apps')  , 'not appear on the home screen'
        d(text='WeChat').click.wait()
        assert d(text="Me").wait.exists(timeout=5000), 'wechat unable to open in 10 secs'
        assert d(text="Discover").wait.exists(timeout=1000), 'wechat unable to open in 10 secs'
        d(className='android.widget.ImageView', index=0).click.wait()
        d(className='android.widget.CheckBox').click.wait()
        d(text='OK(1)').click.wait()
        #d.click('go.png', threshold=0.01)
        d.click('compose.png')
        #d(className='android.widget.EditText').set_text('how are u')
        #d(className='android.widget.Button', text='Send').click.wait()
        #assert d(text="Thanks for your feedback.").wait.exists(timeout=10000) or d(text="Got it - thanks!").wait.exists(timeout=10000), 'msg unable to send in 20 secs'
        if d.exists(className='android.widget.Button', text='Hold to Talk'):
            pass
        else:
            d.click('composeaudio.png')
        d(className='android.widget.Button', text='Hold to Talk').swipe.up(steps=200)
        assert d(className='android.widget.Button', text='Release to send').wait.gone(timeout=10000), 'unable to send msg'
        