from app.database import db
from passlib.hash import bcrypt

users = db["users"]

class UserModel:
    @classmethod
    def criar(cls, username, password):
        if users.find_one({"username": username}):
            return False
        users.insert_one({
            "username": username,
            "hash": bcrypt.hash(password)
        })
        return True

    @classmethod
    def autenticar(cls, username, password):
        user = users.find_one({"username": username})
        if user and bcrypt.verify(password, user["hash"]):
            return True
        return False

    @classmethod
    def listar(cls):
        return list(users.find({}, {"_id": 0, "username": 1}))