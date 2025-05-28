from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["odontoclin"]
atendimentos = db["atendimentos"]

class Atendimento:
    @staticmethod
    def criar(data):
        atendimentos.insert_one({"usuario": data["usuario"], "status": "pendente", "mensagens": []})
    @staticmethod
    def em_andamento(usuario):
        return atendimentos.find_one({"usuario": usuario, "status": "pendente"}) is not None
    @staticmethod
    def registrar_mensagem(usuario, mensagem):
        atendimentos.update_one(
            {"usuario": usuario, "status": "pendente"},
            {"$push": {"mensagens": mensagem}}
        )
    @staticmethod
    def finalizar(usuario):
        atendimentos.update_one(
            {"usuario": usuario, "status": "pendente"},
            {"$set": {"status": "finalizado"}}
        )
    @staticmethod
    def todos_pendentes():
        return list(atendimentos.find({"status": "pendente"}))