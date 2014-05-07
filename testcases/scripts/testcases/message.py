#!/usr/bin/python
# -*- coding:utf-8 -*- 
import unittest
from devicewrapper.android import device as d

class MessageTest(unittest.TestCase):
    def setUp(self):
        super(MessageTest, self).setUp()
        d.wakeup()
        #d.start_activity(action='android.intent.action.DIAL', data='tel:13581739891', flags=0x04000000)
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def tearDown(self):
        d.press('back')
        d.press('back')
        d.press('back')
        d.press('home')

    def testSendMessage1(self):
        assert d.exists(text='Messaging') , 'message app not appear on the home screen'
        #assert d.exists(text='Apps')  , 'apps not appear on the home screen'
        assert 0, 'manunal failure'
        d(text='Messaging').click.wait()
        if not d(text="No conversations.").wait.exists(timeout=3000):
            d(className='android.view.View').long_click()
            if d(text="Check All").wait.exists(timeout=3000):
                d(text="Check All").click.wait()
            d(text="Delete").click.wait()
            d(text="Delete").click.wait()
            assert d(text="No conversations.").wait.exists(timeout=10000)
        d(text='New message').click.wait()
        d(className='android.widget.EditText', index=0).set_text('13581739891')
        assert d(text="13581739891").wait.exists(timeout=10000), 'receiver number input error'            
        d(className='android.widget.EditText', index=1).set_text('Testingongoing')
        assert d(text="Testingongoing").wait.exists(timeout=10000), 'content input error'            
        d(description='Send message').click.wait()
        assert d(text='Received').wait.exists(timeout=20000), 'message unable to send in 20 seconds'
        #assert d(description='Sending failed').wait.exists(timeout=10000), 'message send failed'
        #assert d(text='Failed').wait.exists(timeout=10000), 'message send failed'




            

