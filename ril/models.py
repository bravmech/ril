from app import db

import datetime as dt
from utils import *


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    pw_hash = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(100))

    def __init__(self, name, pw_hash, email):
        self.name = name
        self.pw_hash = pw_hash
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.name


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    state = db.Column(db.String(20)) # enum?
    added = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, content, user_id):
        self.content = content
        self.state = 'unread'
        self.added = dt.datetime.now()
        self.user_id = user_id

    def __repr__(self):
        return '<Item %r>' % self.content


def create_user(username, password, email):
    u = User(username, make_pw_hash(username, password), email)
    db.session.add(u)
    db.session.commit()


def get_user(username):
    return User.query.filter_by(name=username).first()


def get_item(item_id):
    return Item.query.filter_by(id=item_id).first()
