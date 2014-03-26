# -*- coding: utf-8 -*-
"""
    RIL2.0
    ~~~~~~

    RIL taken to the next level.

    :copyright: (c) 2014 by bravmech
"""

from flask import Flask, g
from flask import redirect, url_for, render_template
from flask import session, request, flash
app = Flask(__name__)

import os
import ipdb
import datetime as dt
from sqlite3 import dbapi2 as sqlite3
from utils import *

app.secret_key = 'omsVT1zPKmBhPMEVNlVQvgryp'

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'ril.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))

app.jinja_env.globals.update(isurl=isurl)


def connect_db():
    """Connects to the specific database."""
    conn = sqlite3.connect(app.config['DATABASE'],
                            detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the database tables."""
    if os.path.exists(app.config['DATABASE']):
        return
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def create_user(username, password, email):
    db = get_db()
    db.execute('insert into users(name, pw_hash, email) values (?, ?, ?)',
                [username, make_pw_hash(username, password), email])
    db.commit()


def get_user(username):
    db = get_db()
    cur = db.execute('select id, name, pw_hash, email from users where name = ?',
                        [username])
    return cur.fetchone()


def get_item(item_id):
    db = get_db()
    cur = db.execute('''
        select id, user_id, content, state, added from items
        where id = ?
    ''', [item_id])
    return cur.fetchone()


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
        valid = user and isvalid_pw(username, password, user[2])

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

    user_id = g.user[0]
    content = request.form['content']
    state = 'unread'
    added = dt.datetime.now()

    db = get_db()
    db.execute('''
        insert into items(user_id, content, state, added)
        values (?, ?, ?, ?)
    ''', [user_id, content, state, added])
    db.commit()
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
    db = get_db()
    cur = db.execute('''
        select id, user_id, content, state, added from items
        where state = :state and items.user_id = :user_id
    ''', dict(state=state, user_id=g.user[0]))
    items = cur.fetchall()
    return render_template('list.html', items=items, username=session['username'],
                            state=state)


def verify_item(item_id):
    item = get_item(item_id)
    user_id = item[1]
    if user_id != g.user[0]:
        flash('Please edit your own items.')
        return redirect('/unread')
    return item


@app.route('/check/<int:item_id>')
def check(item_id):
    item = verify_item(item_id)
    db = get_db()
    db.execute("update items set state = 'read' where id = ?", [item[0]])
    db.commit()
    flash('item marked as read')
    return redirect('/unread')


@app.route('/re-add/<int:item_id>')
def re_add(item_id):
    item = verify_item(item_id)
    db = get_db()
    db.execute("update items set state = 'unread' where id = ?", [item[0]])
    db.commit()
    flash('item marked as unread')
    return redirect('/read')


@app.route('/delete/<int:item_id>')
def delete(item_id):
    item = verify_item(item_id)
    db = get_db()
    db.execute("delete from items where id = ?", [item[0]])
    db.commit()
    flash('item deleted')
    return redirect('/read')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
