import re
import hashlib
import hmac
import random
import string


USERNAME_RE = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
def isvalid_username(username):
    return username and USERNAME_RE.match(username)

PASSWORD_RE = re.compile(r'^.{3,20}$')
def isvalid_password(password):
    return password and PASSWORD_RE.match(password)

EMAIL_RE = re.compile('^[\S]+@[\S]+\.[\S]+$')
def isvalid_email(email):
    return not email or EMAIL_RE.match(email)


def make_salt(length=5):
    return ''.join(random.choice(string.letters) for _ in xrange(length))

def make_pw_hash(name, pw, salt=None):
    if salt == None:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def isvalid_pw(name, pw, pw_hash):
    salt = pw_hash.split(',')[1]
    return make_pw_hash(name, pw, salt) == pw_hash

def isurl(text):
    """yep I know, I know"""
    return text.startswith('http')

