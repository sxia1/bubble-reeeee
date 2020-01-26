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

lineStorage = { # Setup for temporary line storage may change depending on support for multiple pages
    # documentID : {
    #     'connectedUsers' : {request.sid},
    #     'lines' : [
    #         [x0, y0, x1, y1, lineWidth, 'rgba(r,g,b,a)']
    #     ]
    # }
}

connectedUsers = {
    # request.sid : documentID
}

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
    if dbtools.authUser(username, password):
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
    if not dbtools.userExists(username): # username unavailable
        flash("Choose a different username")
        return redirect(url_for('signup'))
    elif password == "": # no password entered 
        flash("Enter a password")
        return redirect(url_for('signup'))
    elif password != retyped_pass: # passwords don't match 
        flash("Passwords do not match")
        return redirect(url_for('signup'))
    else:
        if dbtools.addUser(username, password):
            flash("You have successfully registered")
        else: 
            flash("This username is already in use")
            return redirect(url_for('signup'))
    dbtools.authUser(username, password)
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

@app.route('/document/<documentID>')
def documentPage(documentID):
    '''
    Page to display the document
    '''
    docIsPublic = True # Check if the document is public
    if docIsPublic:
        return render_template("document.html")
    if "user" in session:
        userHasPermission = True # Check if the current user has access to the document
        if userHasPermission:
            return render_template("document.html")
        else: # User does not have permission to view the document
            return redirect("/")
    return redirect("/login") # User is not logged in, redirect to login

@socketio.on('connect', namespace = '/document')
def connectToDoc():
    print(f"A user has connected to a document page with sid {request.sid}")

@socketio.on('disconnect', namespace = '/document')
def disconnectFromDoc():
    print(f"{request.sid} disconnected")
    lineStorage[connectedUsers[request.sid]]['connectedUsers'].remove(request.sid)
    print(lineStorage[connectedUsers[request.sid]]['connectedUsers'])
    print(f"{len(lineStorage[connectedUsers[request.sid]]['connectedUsers'])} users remaining in {connectedUsers[request.sid]}")
    if len(lineStorage[connectedUsers[request.sid]]['connectedUsers']) == 0:
        lineStorage.pop(connectedUsers[request.sid])
    connectedUsers.pop(request.sid)

@socketio.on('joinDocument', namespace = '/document')
def joinDocument(documentID):
    docIsPublic = True # Check if the document is public
    successfulJoin = False
    if docIsPublic:
        join_room(documentID)
        successfulJoin = True
    elif "user" in session:
        userHasPermission = True # Check if the current user has access to the document
        if userHasPermission:
            join_room(documentID)
            successfulJoin = True
        else:
            send('This user does not have permission to access the requested document.')
    else:
        send('This user is not logged in.')
    if successfulJoin:
        if documentID not in lineStorage: # Document not being viewed yet
            lineStorage[documentID] = {
                'connectedUsers' : {request.sid},
                'lines' : []
            }
        else: # Document already being viewed
            lineStorage[documentID]['connectedUsers'].add(request.sid)
            emit('lines', lineStorage[documentID]['lines'])
        connectedUsers[request.sid] = documentID

@socketio.on('newLine', namespace = '/document')
def newLine(line):
    documentID = connectedUsers[request.sid]
    lineStorage[documentID]['lines'].append(line)
    emit('newLine', line, broadcast = True, include_self = False, room = documentID)

@socketio.on('connect', namespace = '/socketioTest')
def userConnect():
    join_room("testRoom")
    print(f"A user has connected to the test page with sid {request.sid}")

@socketio.on('sendHi', namespace = '/socketioTest')
def sendHi():
    emit('receiveHi', broadcast = True, room = 'testRoom')

if __name__ == '__main__':
    app.debug = True
    socketio.run(app)
