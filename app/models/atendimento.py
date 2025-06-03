from app.database import db
from datetime import datetime

atendimentos = db["atendimentos"]

class AtendimentoModel:
    @classmethod
    def criar(cls, dados):
        dados.setdefault("status", "pendente")
        dados.setdefault("mensagens", [])
        dados.setdefault("criado_em", datetime.now().strftime("%Y-%m-%d %H:%M"))
        atendimentos.update_one(
            {"usuario": dados["usuario"], "status": "pendente"},
            {"$setOnInsert": dados},
            upsert=True
        )

    @classmethod
    def em_andamento(cls, usuario):
        return atendimentos.find_one({"usuario": usuario, "status": "pendente"})

    @classmethod
    def registrar_mensagem(cls, usuario, mensagem):
        atendimentos.update_one(
            {"usuario": usuario, "status": "pendente"},
            {"$push": {"mensagens": {"texto": mensagem, "momento": datetime.now().strftime("%Y-%m-%d %H:%M")}}}
        )

    @classmethod
    def todos_pendentes(cls):
        return list(atendimentos.find({"status": "pendente"}))

    @classmethod
    def finalizar(cls, usuario):
        atendimentos.update_one(
            {"usuario": usuario, "status": "pendente"},
            {"$set": {"status": "finalizado", "finalizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")}}
        )