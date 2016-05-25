# -*- coding:utf-8 -*-
import unittest
from app import create_app,db
from app.models import User,Role
from flask import url_for
import re

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self,app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.text_client(use_cookies=True)

    def teardown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue(b'stranger' in response.data)

    def test_register_and_login(self):
        # register a new account
        response = self.client.post(url_for('auth.register'),data ={
            'email': 'john@sina.com',
            'username': 'john',
            'password':'cat',
            'password2':'cat'
        } )
        self.assertTrue(response.status_code == 302)

        #登录
        response = self.client.post(url_for('auth.login'),data={
            'email': 'john@sina.com',
            'password': 'cat'
        },follow_redirects=True)
        self.assertTrue(re.search(b'您好，\s+john',response.data))
        self.assertTrue(
            b'您还没有激活您的账户。' in response.data
        )

        #发送激活信息
        user = User.query.filter_by(email='john@sina.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm',token=token),
                                   follow_redirects=True)
        self.assertTrue(b'您已经激活了账户！' in response.data)

        #退出登录
        response = self.client.get(url_for('auth.logout'),follow_redirects=True)
        self.assertTrue(b'您已经退出登录.' in response.data)