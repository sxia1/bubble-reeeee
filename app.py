import os, random, json, urllib
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from flask import Flask, render_template, request, session, url_for, redirect, flash
from util import Database

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(32)
socketio = SocketIO(app)

app.config["MONGO_DBNAME"] = os.environ["databaseName"]
app.config["MONGO_URI"] = os.environ["mongoURI"]

dbtools = Database.DBTools(app)

print(dbtools.createDocID())


@app.route('/')
def root():
    guest = 'user' not in session
    user = None
    if not guest: user = session['user']
    return render_template("base.html", guest = guest, user = user)

@app.route('/login')
def login():
    '''
    login page
    '''
    guest = 'user' not in session
    if not guest:
        return redirect('/')
    return render_template('login.html', guest = guest)

@app.route('/login_auth', methods = ['POST'])
def login_auth():
    '''
    login authorization
    '''
    username = request.form['username']
    password = request.form['password']
    if db.auth_user(username, password):
        session['user'] = username
        flash("You have logged in")
        return redirect('/')
    else:
        flash("Invalid username and password combination")
        return render_template('login.html')

@app.route('/signup')
def signup():
    '''
    signup page
    '''
    guest = 'user' not in session
    return render_template("signup.html", guest = guest)

@app.route('/signup_auth', methods = ['POST'])
def register_auth():
    '''
    signup authorization
    '''
    username = request.form['username']
    password = request.form['password']
    retyped_pass = request.form['repass']
    if username == "": # no username entered
        flash("Enter a username")
        return redirect(url_for('signup'))
    if not db.registered(username): # username unavailable
        flash("Choose a different username")
        return redirect(url_for('signup'))
    elif password == "": # no password entered 
        flash("Enter a password")
        return redirect(url_for('signup'))
    elif password != retyped_pass: # passwords don't match 
        flash("Passwords do not match")
        return redirect(url_for('signup'))
    else:
        if db.add_user(username, password):
            flash("You have successfully registered")
        else: 
            flash("This username is already in use")
            return redirect(url_for('signup'))
    db.auth_user(username, password)
    session['user'] = username
    return redirect('/')

@app.route('/logout')
def logout():
    '''
    logout
    '''
    if 'user' in session:
        session.pop('user')
    return redirect('/')

@app.route('/socketioTest')
def socketioTest():
    '''
    Test page for SocketIO
    '''
    return render_template("socketioTest.html")

@socketio.on('connect')
def userConnect():
    join_room("testRoom")
    print("A user has connected with sid {request.sid}")

@socketio.on('sendHi')
def sendHi():
    emit('receiveHi', broadcast = True, room = 'testRoom')

if __name__ == '__main__':
    app.debug = True
    socketio.run(app)
