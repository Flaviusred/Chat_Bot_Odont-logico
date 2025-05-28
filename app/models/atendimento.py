from app.database import db

atendimentos = db["atendimentos"]

class AtendimentoModel:
    @staticmethod
    def criar(data):
        return atendimentos.insert_one(data)

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