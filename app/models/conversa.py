from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["odontoclin"]
conversas = db["conversas"]

class Conversa:
    @staticmethod
    def criar(usuario, msg_usuario, resposta_bot):
        conversas.insert_one({
            "usuario": usuario,
            "mensagem": msg_usuario,
            "resposta": resposta_bot
        })
    @staticmethod
    def todos():
        return list(conversas.find())