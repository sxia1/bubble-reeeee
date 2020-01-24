import random, os, string
from flask_pymongo import PyMongo
from passlib.hash import sha256_crypt # password hashing -- sha256_crypt.hash(hash_this)

CHARSET = string.ascii_uppercase + string.ascii_lowercase + string.digits

class DBTools:
	def __init__(self, app):
		self.mongo = PyMongo(app)

	def createDocID(self):
		ID = ''.join(random.choices(CHARSET, 8))
		while(self.mongo.db.docs.find({'docID': ID}).count() != 0):
			ID = ''.join(random.choices(CHARSET, 8))
		return ID

	def addUser(self, username, password):
		self.mongo.db.users.insert({
			'username' : username,
			'password' : sha256_crypt.hash(password)
		})
	
	def userExists(self, username):
		self.mongo.db.users.find({'username' : username})

	def authPassword(self, username, password):
		pwd = self.mongo.db.users.find({'username' : username})['password']
		return sha256_crypt.verify(password, pwd)

	def addDoc(self, username, docName, overlay):
		self.mongo.db.docs.insert({
			'owner' : username,
			'docID' : createDocID()
			'document_name' : docName,
			'overlay' : overlay
		})

	def addCollab(self, docID, collab, start, duration):
		self.mongo.db.collabs.insert({
			'docID' : docID,
			'collab' : collab,
			'start' : start,
			'duration' : duration
		})

	def removeCollab(self, docID, collab):
		self.mongo.db.collabs.remove({
			'docID' : docID,
			'collab' : collab,
			'start' : start,
			'duration' : duration
		})


	def updateOverlay(self, docID, newOverlay):
		self.mongo.db.docs.updateOne(
			{'docID' : docID},
			{$set:
				{'overlay': newOverlay}
			}
		)

	def checkAuth(self, username, docID):
		owner = self.mongo.db.docs.find({'owner' : username, 'docID' : docID}).count()
		collab = self.mongo.db.collab.find('docID' : docID, 'collab': username).count()
		return owner == 1 or collab == 1


