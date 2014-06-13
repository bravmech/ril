from flask import g
from flask import redirect, url_for, render_template
from flask import session, request, flash
from ril import app

import os
from ipdb import set_trace
import datetime as dt
from functools import wraps

from utils import *
from models import *


app.jinja_env.globals.update(isurl=isurl)


# =decorators custom

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'user', None):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def verify_item(f):
    """ checks whether the item belongs to logged user
    won't actually fire if the user isn't logged """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        item_id = request.form['item_id']
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
        user = get_user(username)
        valid = user and isvalid_pw(username, password, user.pw_hash)

    if not valid:
        error = 'Invalid login.'
        return render_template('login.html', username=username, error=error)
    session['username'] = username
    return redirect(url_for('welcome'))


@app.route('/welcome/')
@login_required
def welcome():
    return render_template('welcome.html', name=session['username'])


@app.route('/logout/')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/new/', methods=['GET', 'POST'])
@login_required
def new_item():
    if request.method == 'GET':
        return render_template('new.html', username=session['username'])

    item = Item(content=request.form['content'], user_id=g.user.id)
    db.session.add(item)
    db.session.commit()

    flash('new item added')
    return redirect('/unread')


@app.route('/')
@login_required
def index():
    return redirect('/unread')


@app.route('/unread/')
@login_required
def show_unread():
    # ipdb.set_trace()
    items = ( Item.query
        .filter_by(state='unread', user_id=g.user.id)
        .order_by(Item.added.desc())
    )
    return render_template('unread.html', items=items,
                            username=session['username'], state='unread')


@app.route('/read/')
@login_required
def show_read():
    items = ( Item.query
        .filter_by(state='read', user_id=g.user.id)
        .order_by(Item.added.desc())
    )
    return render_template('read.html', items=items,
                            username=session['username'])


@app.route('/check', methods=['POST'])
@verify_item
@login_required
def check():
    item_id = request.form['item_id']
    item = get_item(item_id)
    item.state = 'read'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as read')
    return url_for('show_unread')


@app.route('/re-add', methods=['POST'])
@verify_item
@login_required
def re_add():
    item_id = request.form['item_id']
    item = get_item(item_id)
    item.state = 'unread'
    item.added = dt.datetime.now()
    db.session.commit()
    flash('item marked as unread')
    return url_for('show_read')


@app.route('/delete', methods=['POST'])
@verify_item
@login_required
def delete():
    item_id = request.form['item_id']
    item = get_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('item deleted')
    return url_for('show_read')
