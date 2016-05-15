# -*- coding: utf-8 -*-

import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug import check_password_hash, generate_password_hash
from datetime import datetime
import time
import random


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'jude.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    TIME_STAMP = int(time.time())
))
app.config.from_envvar('JUDE_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def assign_entries(entries):
    senders = [entry['sender'] for entry in entries]
    ids = [entry['id'] for entry in entries]
    random.shuffle(senders)
    return zip(senders,ids)

@app.route('/upupdowndownleftrightleftrightbaba')
def pass_one_day():
    app.config['TIME_STAMP']+=24*60*60
    print datetime.utcfromtimestamp(app.config['TIME_STAMP']).strftime('%Y-%m-%d')
    db = get_db()
    cur = db.execute('select * from entries where date < ?',[datetime.utcfromtimestamp(app.config['TIME_STAMP']).strftime('%Y-%m-%d')])
    entries = cur.fetchall()
    no_reciever_entries = []
    for entry in entries:
        if entry['reciever'] != "":
            db.execute("update entries set recieved = 1 where id = ?",[entry['id']])
        else:
            no_reciever_entries.append(entry)
    assignment = assign_entries(no_reciever_entries)
    for _reciever,_id in assignment:
        db.execute("update entries set reciever = ?, recieved = 1 where id = ?",[_reciever,_id])
    db.commit()
    return 'Welcome to %s'%datetime.utcfromtimestamp(app.config['TIME_STAMP']).strftime('%Y-%m-%d')

@app.route('/whoisyourdaddy')
def all_entries():
    db = get_db()
    cur = db.execute('select sender,reciever,text,date,recieved from entries order by id desc')
    entries = cur.fetchall()
    return render_template('all_entries.html', entries=entries)

@app.route('/ohmygod')
def initdb_command():
    """Creates the database tables."""
    init_db()
    return 'You have created the world.'


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

def get_user_id(username):
    user_info = get_db().execute('select * from user where username = ?',
                          [username]).fetchall()
    user = user_info[0] if user_info  else None

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (sender,reciever,text,date,recieved) values (?,?,?,?,?)',
               [session['username'],request.form['reciever'], request.form['text'],datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d'),False])
    db.commit()
    flash('New entry was successfully sent')
    return redirect(url_for('user_entries',username = session['username']))

@app.route('/<username>')
def user_entries(username):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.execute('select sender, text, date from entries where reciever = ? and recieved = 1 order by id desc',[session['username']])
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/') 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('user_entries',username = session['username']))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_info = get_db().execute('select * from user where username=?',[username]).fetchall()
        user = user_info[0] if user_info else None
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],password):
            error = 'invalid password'
        else:
            session['logged_in'] = True
            session['username'] = user['username']
            flash('You were logged in')
            return redirect(url_for('user_entries', username=username))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET','POST'])
def register():
    """Registers the user."""
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''insert into user (
              username, pw_hash) values (?, ?)''',
              [request.form['username'],
               generate_password_hash(request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect('/')

if __name__ == '__main__':
    app.run()
