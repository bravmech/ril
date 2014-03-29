from flask import g
from flask import redirect, url_for, render_template
from flask import session, request, flash
from ril import app

import os
import ipdb
import datetime as dt
from functools import wraps

from utils import *
from models import *


app.jinja_env.globals.update(isurl=isurl)


# =decorators custom

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def verify_item(f):
    """checks whether the item belongs to logged user"""
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


@login_required
@app.route('/welcome/')
def welcome():
    return render_template('welcome.html', name=session['username'],
                            unread_page='/unread')


@login_required
@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@login_required
@app.route('/new/', methods=['GET', 'POST'])
def new_item():
    if request.method == 'GET':
        return render_template('new.html', username=session['username'])

    item = Item(content=request.form['content'], user_id=g.user.id)
    db.session.add(item)
    db.session.commit()

    flash('new item aded')
    return redirect('/unread')


@login_required
@app.route('/')
def index():
    return redirect('/unread')


@login_required
@app.route('/read/', defaults={'state': 'read'})
@app.route('/unread/', defaults={'state': 'unread'})
def show_list(state):
    """showing both read and unread in one function since
    they are too similar. kinda weird i know, needs refactoring."""
    # ipdb.set_trace()
    items = Item.query.filter_by(state=state, user_id=g.user.id)
    return render_template('list.html', items=items, username=session['username'],
                            state=state)


@login_required
@verify_item
@app.route('/check/<int:item_id>')
def check(item_id):
    item = get_item(item_id)
    item.state = 'read'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as read')
    return redirect('/unread')


@login_required
@verify_item
@app.route('/re-add/<int:item_id>')
def re_add(item_id):
    item = get_item(item_id)
    item.state = 'unread'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as unread')
    return redirect('/read')


@login_required
@verify_item
@app.route('/delete/<int:item_id>')
def delete(item_id):
    item = get_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('item deleted')
    return redirect('/read')
