import random, os, string
from flask_pymongo import PyMongo
from passlib.hash import sha256_crypt # password hashing -- sha256_crypt.hash(hash_this)

CHARSET = string.ascii_uppercase + string.ascii_lowercase + string.digits

class DBTools:
	def __init__(self, app):
		self.mongo = PyMongo(app)

	def createDocID(self):
		ID = ''.join(random.choice(CHARSET) for x in range(8))
		while(self.mongo.db.docs.find({'docID': ID}).limit(1).count() != 0):
			ID = ''.join(random.choice(CHARSET) for x in range(8))
		return ID

	def addUser(self, username, password):
		if not self.userExists(username):
			self.mongo.db.users.insert({
				'username' : username,
				'password' : sha256_crypt.hash(password)
			})
			return True
		return False
	
	def userExists(self, username):
		return self.mongo.db.users.find({'username' : username}).limit(1).count() == 1

	def authUser(self, username, password):
		c = self.mongo.db.users.find({'username' : username}).limit(1)
		if c.count() == 0:
			return False
		pwd = c[0]['password']
		return sha256_crypt.verify(password, pwd)

	def addDoc(self, username, docName, fname, size):
		ID = self.createDocID()
		self.mongo.db.docs.insert({
			'owner' : username,
			'docID' : ID,
			'length' : len(fname),
			'public' : False,
			'document_name' : docName,
			'overlay' : None
		})
		for x in range(len(fname)):
			self.mongo.db.img.insert({
				'docID' : ID,
				'num' : x,
				'size' : size[x],
				'data' : fname[x]
			})
		return ID

	def checkLength(self, docID):
		doc = self.mongo.db.docs.find({'docID' : docID})
		if doc:
			return doc[0]['length']
		return 0

	def addCollab(self, username, docID, collab, write):
		if self.mongo.db.docs.find({'owner' : username, 'docID' : docID}).limit(1).count() == 0:
			return False
		self.mongo.db.collabs.insert({
			'docID' : docID,
			'collab' : collab,
			'write' : write
		})

	def removeCollab(self, username, docID, collab):
		if self.mongo.db.docs.find({'owner' : username, 'docID' : docID}).limit(1).count() == 0:
			return False
		self.mongo.db.collabs.remove({
			'docID' : docID,
			'collab' : collab
		})

	def updateOverlay(self, docID, newOverlay):
		self.mongo.db.docs.update(
			{'docID' : docID},
			{'$set': {
				'overlay' : newOverlay
			}}
		)

	def getOverlay(self, docID):
		doc = self.mongo.db.docs.find({'docID' : docID}).limit(1)
		if doc:
			return doc[0]['overlay']

	def checkAuth(self, username, docID):
		doc = self.mongo.db.docs.find({'docID': docID}).limit(1)[0]
		collab = self.mongo.db.collabs.find({'docID' : docID, 'collab': username}).count()
		return doc['owner'] == username or collab

	def checkPublic(self, docID):
		doc = self.mongo.db.docs.find({'docID': docID}).limit(1)
		if doc:
			return doc[0]['public']
		return False

	def setPublic(self, username, docID, public):
		if self.mongo.db.docs.find({'owner' : username, 'docID' : docID}).limit(1).count() == 0:
			return False
		doc = self.mongo.db.docs.find({'docID': docID}).limit(1)
		doc.self.mongo.db.docs.update(
			{'docID' : docId},
			{'$set' : {
				'public' : public
			}}
		)

	def checkWrite(self, username, docID):
		doc = self.mongo.db.collabs.find({'docID' : docID, 'collab' : username}).limit(1)
		return (doc.count() != 0 and doc[0]['write']) or self.mongo.db.docs.find({'owner' : username, 'docID' : docID}).limit(1).count() != 0

	def getPage(self, docID, num):
		page = self.mongo.db.img.find({'docID' : docID, 'num' : num})
		if page:
			return page.limit(1)[0]
		return None

	def getAllDocs(self, username):
		c = self.mongo.db.docs.find({'owner' : username})
		ret = []
		for each in c:
			ret.append((each['docID'], each['document_name']))
		return ret
