import random, os
from flask_pymongo import PyMongo
from passlib.hash import sha256_crypt # password hashing -- sha256_crypt.hash(hash_this)

class DBTools:
	def __init__(self, app):
		self.mongo = PyMongo(app)
