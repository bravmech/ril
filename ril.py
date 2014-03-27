# -*- coding: utf-8 -*-
"""
    RIL2.0
    ~~~~~~

    RIL to be taken to the next level.

    :copyright: (c) 2014 by bravmech
"""

from flask import Flask, g
from flask import redirect, url_for, render_template
from flask import session, request, flash
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)

import os
import ipdb
import datetime as dt
from functools import wraps

from utils import *


# basically it's config
app.secret_key = 'omsVT1zPKmBhPMEVNlVQvgryp'
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'DATABASE_URL',
        'sqlite:////%s/ril.db' % app.root_path),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.jinja_env.globals.update(isurl=isurl)
db = SQLAlchemy(app)


# =db stuff

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


# =decorators custom

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def verify_item(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        item_id = kwargs['item_id']
        item = get_item(item_id)
        if g.user and item.user_id != g.user.id:
            flash('Please edit your own items.')
            return redirect('/unread')
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def load_user():
    if 'username' not in session:
        return
    g.user = get_user(session['username'])


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/unread')
        return render_template('signup.html')

    username = request.form['username']
    password = request.form['password']
    pw_verify = request.form['pw_verify']
    email = request.form['email']
    valid = True
    if not isvalid_username(username):
        error_username = "That's not a valid username."
        valid = False
    if not isvalid_password(password):
        error_password = "That wasn't a valid password."
        valid = False
    elif password != pw_verify:
        error_verify= "Your passwords didn't match."
        valid = False
    if not isvalid_email(email):
        error_email = "That's not a valid email."
        valid = False
    if get_user(username):
        error_user = 'That user already exists.'
        valid = False

    if not valid:
        params = dict(locals()) # hackish
        return render_template('signup.html', **params)
    create_user(username, password, email)
    session['username'] = username
    flash('New user was sussessfully created!')
    return redirect(url_for('welcome'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/unread')
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    valid = True
    if not username:
        valid = False
    else:
        user = get_user(username) # id, name, pw_hash, email
        valid = user and isvalid_pw(username, password, user.pw_hash)

    if not valid:
        error = 'Invalid login.'
        return render_template('login.html', username=username, error=error)
    session['username'] = username
    return redirect(url_for('welcome'))


@app.route('/welcome/')
def welcome():
    if 'username' in session:
        return render_template('welcome.html', name=session['username'],
                                unread_page='/unread')
    return redirect(url_for('signup'))


@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/new/', methods=['GET', 'POST'])
def new_item():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('new.html', username=session['username'])

    item = Item(content=request.form['content'], user_id=g.user.id)
    db.session.add(item)
    db.session.commit()

    flash('new item aded')
    return redirect('/unread')


@app.route('/')
def index():
    return redirect('/unread')


@app.route('/read/', defaults={'state': 'read'})
@app.route('/unread/', defaults={'state': 'unread'})
def show_list(state):
    """showing both read and unread in one function since
    they are too similar. kinda weird i know, needs refactoring."""
    if 'username' not in session:
        return redirect(url_for('login'))
    # ipdb.set_trace()
    items = Item.query.filter_by(state=state, user_id=g.user.id)
    return render_template('list.html', items=items, username=session['username'],
                            state=state)


@verify_item
@app.route('/check/<int:item_id>')
def check(item_id):
    item = get_item(item_id)
    item.state = 'read'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as read')
    return redirect('/unread')


@verify_item
@app.route('/re-add/<int:item_id>')
def re_add(item_id):
    item = get_item(item_id)
    item.state = 'unread'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as unread')
    return redirect('/read')


@verify_item
@app.route('/delete/<int:item_id>')
def delete(item_id):
    item = get_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('item deleted')
    return redirect('/read')


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
