from pymongo import MongoClient
import os
from passlib.hash import bcrypt

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient("mongodb://localhost:27017")
db = client["gestor_db"]
users = db["users"]
