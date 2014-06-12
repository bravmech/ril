import os
import unittest
import re

from flask import escape

from ril import app, db
from ril.models import *

from ipdb import set_trace


class RilTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(
            os.path.join(app.root_path, 'test.db'))
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.app.post('/login/', data=dict(
            username=username,
            password=password,
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout/', follow_redirects=True)


class TestSignup(RilTestCase):
    def signup(self, username, password, pw_verify, email=''):
        return self.app.post('/signup/', data=dict(
            username=username,
            password=password,
            pw_verify=pw_verify,
            email=email
        ), follow_redirects=True)

    def test_valid(self):
        username = 'joe'
        password = 'pwd'
        ret = self.signup(username, password, password)
        assert re.search('Welcome', ret.data, re.I) and username in ret.data
        assert get_user(username)

    def test_valid_with_email(self):
        username = 'joe'
        password = 'pwd'
        email = 'joe@doe.com'
        ret = self.signup(username, password, password, email)
        assert re.search('Welcome', ret.data, re.I) and username in ret.data
        user = get_user(username)
        assert user and user.email == email

    def test_invalid_username(self):
        username = 'jo'
        password = 'pwd'
        ret = self.signup(username, password, password)
        assert re.search('That&#39;s not a valid username.', ret.data, re.I)

    def test_invalid_password(self):
        username = 'joe'
        password = 'p'
        ret = self.signup(username, password, password)
        assert re.search('That wasn&#39;t a valid password', ret.data, re.I)

    def test_invalid_verify_password(self):
        password1 = 'pwd1'
        password2 = 'pwd2'
        ret = self.signup('joe', password1, password2)
        assert re.search('Your passwords didn&#39;t match.', ret.data, re.I)

    def test_invalid_email(self):
        username = 'joe'
        password = 'pwd'
        email = 'email'
        ret = self.signup(username, password, password, email)
        assert re.search('That&#39;s not a valid email.', ret.data, re.I)

    def test_invalid_user_exists(self):
        username = 'joe'
        password = 'pwd'
        create_user(username, password)
        ret = self.signup(username, password, password)
        assert re.search('That user already exists.', ret.data, re.I)

    def test_logged_in(self):
        username = 'joe'
        password = 'pwd'
        create_user(username, password)
        self.login(username, password)
        ret = self.app.get('/signup/', follow_redirects=True)
        assert re.search('ril unread', ret.data, re.I)

    def test_get_method(self):
        ret = self.app.get('/signup/', follow_redirects=True)
        assert re.search('Signup', ret.data, re.I)


class TestLogin(RilTestCase):
    def test_logout(self):
        username = 'joe'
        password = 'pwd'
        user = create_user(username, password)
        ret = self.login(username, password)
        assert re.search('Welcome', ret.data, re.I)
        ret = self.logout()
        assert re.search('Login', ret.data, re.I)

    def test_repeated_login(self):
        username = 'joe'
        password = 'pwd'
        u = create_user(username, password)
        self.login(username, password)
        ret = self.login(username, password)
        assert re.search('ril unread', ret.data, re.I)

    def test_index_redirect1(self):
        ret = self.app.get('/', follow_redirects=True)
        assert re.search('Login', ret.data, re.I)

    def test_index_redirect2(self):
        username = 'joe'
        password = 'pwd'
        u = create_user(username, password)
        self.login(username, password)
        ret = self.app.get('/', follow_redirects=True)
        assert re.search('ril unread', ret.data, re.I)

    def test_required_login(self):
        ret = self.app.get('/unread/', follow_redirects=True)
        assert re.search('Login', ret.data, re.I)

    def test_invalid1(self):
        username = ''
        password = 'pwd'
        ret = self.login(username, password)
        assert re.search('Invalid login.', ret.data, re.I)

    def test_invalid2(self):
        username = 'joe'
        password = 'pwd'
        ret = self.login(username, password)
        assert re.search('Invalid login.', ret.data, re.I)

    def test_invalid3(self):
        username = 'joe'
        password1 = 'pwd1'
        password2 = 'pwd2'
        create_user(username, password1)
        ret = self.login(username, password2)
        assert re.search('Invalid login.', ret.data, re.I)


class TestItem(RilTestCase):
    def new(self, content):
        return self.app.post('/new/', data=dict(
            content=content
        ), follow_redirects=True)

    def create_user_and_login(self, username, password):
        user = create_user(username, password)
        self.login(username, password)

    def test_new_get_method(self):
        self.create_user_and_login('joe', 'pwd')
        ret = self.app.get('/new/', follow_redirects=True)
        assert re.search('New item', ret.data, re.I)

    def test_new(self):
        self.create_user_and_login('joe', 'pwd')
        item_content = "joe's item"
        ret = self.new(item_content)
        assert re.search(escape(item_content), ret.data, re.I)

    def test_check(self):
        self.create_user_and_login('joe', 'pwd')
        item_content = "joe's item"
        self.new(item_content)
        # redirect to unread
        ret = self.app.post('/check', data=dict(
            item_id=1 # hardcoded
        ), follow_redirects=True)
        assert not re.search(escape(item_content), ret.data, re.I)
        ret = self.app.get('/read/', follow_redirects=True)
        assert re.search(escape(item_content), ret.data, re.I)


if __name__ == '__main__':
    unittest.main()
