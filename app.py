import os, random, json, urllib, sys, io
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from flask import Flask, render_template, request, session, url_for, redirect, flash, make_response, send_file
from util import Database
from pdf2image import convert_from_bytes
from bson import Binary
from PIL import Image

from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(32)
socketio = SocketIO(app)

app.config["MONGO_DBNAME"] = os.environ["databaseName"]
app.config["MONGO_URI"] = os.environ["mongoURI"]

dbtools = Database.DBTools(app)

lineStorage = { # Setup for temporary line storage may change depending on support for multiple pages
    # documentID : {
    #     'connectedUsers' : {request.sid},
    #     'write' : {request.sid},
    #     'lines' : [
    #         [page, x0, y0, x1, y1, lineWidth, 'rgba(r,g,b,a)' or 'e']
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
	if not guest:
		user = session['user']
		docs = dbtools.getAllDocs(user)
		return render_template("base.html", guest = guest, user = user, docs = docs)
	return render_template("base.html", guest = guest, user = user, docs = None)

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
    if dbtools.userExists(username): # username unavailable
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

@app.route('/uploadDoc', methods=['POST'])
def uploadDoc():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(url_for('root'))
		print(request.form)
		pdf = request.files['file'].read()
		print(f"File length: {len(pdf)}")
		img = convert_from_bytes(pdf, fmt='png', size=(1000, None))
		if not request.form['docName']:
			docName = 'untitled'
		else:
			docName = request.form['docName']
		bson_list = []
		size_list = []
		for each in img:
			size_list.append(each.size)
			bson_list.append(each.tobytes())
		ID = dbtools.addDoc(session['user'], docName, bson_list, size_list)
		return redirect('/document/' + ID)

@app.route('/socketioTest')
def socketioTest():
    '''
    Test page for SocketIO
    '''
    return render_template("socketioTest.html")

def serve_pil_image(pil_img):
	img_io = io.BytesIO()
	pil_img.save(img_io, 'PNG', quality=70)
	img_io.seek(0)
	return send_file(img_io, mimetype='image/png')

@app.route('/image/<documentID>')
def get_image(documentID):
	num = request.args.get('num', type=int)
	byteimg = dbtools.getPage(documentID, num)
	png = Image.frombytes("RGB", byteimg['size'], byteimg['data'])
	#png.fromstring(byteimg['data'])
	#img = Image.new(mode='RGB', data=byteimg['data'], size=byteimg['size'])
	#response = make_response(byteimg['data'])
	#response = send_file(io.BytesIO(png), mimetype='image/png', attachment_filename)
	#response.headers['Content-Type'] = 'image/png'
	#response.headers['Content-Disposition'] = 'inline'
	return serve_pil_image(png)
	

@app.route('/document/<documentID>')
def documentPage(documentID):
	'''
	Page to display the document
	'''
	docIsPublic = dbtools.checkPublic(documentID)
	guest = 'user' not in session
	user = None
	if not guest:
		user = session['user']
	if docIsPublic:
		length = dbtools.checkLength(documentID)
		URLS = []
		DIMENSIONS = []
		for x in range(length):
			URLS.append(documentID + '?num=' + str(x))
			DIMENSIONS.append(dbtools.getPage(documentID, x)['size'])
		print(dbtools.checkPublic(documentID))
		return render_template("document.html", guest = guest, user = user, URLS = zip(URLS,DIMENSIONS), detail = dbtools.getDoc(documentID))
	if "user" in session:
		userHasPermission = dbtools.checkAuth(session['user'], documentID)
		print(dbtools.checkPublic(documentID), dbtools.checkOwner(user,documentID))
		if userHasPermission:
			length = dbtools.checkLength(documentID)
			URLS = []
			DIMENSIONS = []
			for x in range(length):
				URLS.append(documentID + '?num=' + str(x))
				DIMENSIONS.append(dbtools.getPage(documentID, x)['size'])
			print(dbtools.checkPublic(documentID), dbtools.checkOwner(user,documentID))
			return render_template("document.html", guest = guest, user = user, URLS = zip(URLS,DIMENSIONS), detail = dbtools.getDoc(documentID))
		else:# User does not have permission to view the document
			return redirect("/")
	return redirect("/login") # User is not logged in, redirect to login

@socketio.on('connect', namespace = '/document')
def connectToDoc():
    print(f"A user has connected to a document page with sid {request.sid}")

@socketio.on('disconnect', namespace = '/document')
def disconnectFromDoc():
    currDocID = connectedUsers[request.sid]
    print(f"{request.sid} disconnected")
    lineStorage[currDocID]['connectedUsers'].remove(request.sid)
    print(lineStorage[currDocID]['connectedUsers'])
    print(f"{len(lineStorage[currDocID]['connectedUsers'])} users remaining in {currDocID}")
    if len(lineStorage[currDocID]['connectedUsers']) == 0:
        print('Saved overlay.')
        dbtools.updateOverlay(currDocID, lineStorage[currDocID]['lines'])
        lineStorage.pop(currDocID)
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
            receivedLines = dbtools.getOverlay(documentID)
            if receivedLines == None:
                receivedLines = []
            lineStorage[documentID] = {
                'connectedUsers' : {request.sid},
                'write' : set(),
                'lines' : receivedLines
            }
        else: # Document already being viewed
            lineStorage[documentID]['connectedUsers'].add(request.sid)
        emit('lines', lineStorage[documentID]['lines'])
        connectedUsers[request.sid] = documentID
        if 'user' in session and dbtools.checkWrite(session['user'], documentID):
            lineStorage[documentID]['write'].add(request.sid)
            emit('enableDraw')
                

@socketio.on('newLine', namespace = '/document')
def newLine(line):
    documentID = connectedUsers[request.sid]
    if request.sid not in lineStorage[documentID]['write']:
        send('You are not permitted to write in this document.')
    else:
        lineStorage[documentID]['lines'].append(line)
        emit('newLine', line, broadcast = True, include_self = False, room = documentID)

@socketio.on('addCollab', namespace = '/document')
def addCollab(data):
    # data = [collaboratorUsername, hasWriteAccess]
    if 'user' not in session or request.sid not in connectedUsers:
        send('Collaborator not added.')
        return
    dbtools.addCollab(session['user'], connectedUsers[request.sid], data[0], data[1])
    send('Collaborator added.')

@socketio.on('removeCollab', namespace = '/document')
def removeCollab(collaborator):
    if 'user' not in session or request.sid not in connectedUsers:
        send('Collaborator not removed.')
        return
    dbtools.addCollab(session['user'], connectedUsers[request.sid], collaborator)
    send('Collaborator removed.')

@socketio.on('setVisibility', namespace = '/document')
def setPublic(public):
    if 'user' not in session or request.sid not in connectedUsers:
        send('Collaborator not removed.')
        return
    if type(public) != type(True):
        send('Invalid data.')
        return
    print(dbtools.checkPublic(connectedUsers[request.sid]))
    print(public)
    dbtools.setPublic(session['user'], connectedUsers[request.sid], public)
    print(dbtools.checkPublic(connectedUsers[request.sid]))
    send('Visibility not changed.')

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
