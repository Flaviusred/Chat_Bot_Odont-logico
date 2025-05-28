from app.database import db

conversas = db["conversas"]

class ConversaModel:
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