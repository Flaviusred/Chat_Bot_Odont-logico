from app.database import db
from bson import ObjectId

agendamentos = db["agendamentos"]

class AgendamentoModel:
    colecao = db["agendamentos"]

    @classmethod
    def criar(cls, dados):
        return cls.colecao.insert_one(dados)

    @classmethod
    def listar(cls, filtro=None):
        filtro = filtro or {}
        return list(cls.colecao.find(filtro))

    @classmethod
    def obter(cls, agendamento_id):
        return cls.colecao.find_one({"_id": ObjectId(agendamento_id)})

    @classmethod
    def cancelar(cls, agendamento_id):
        return cls.colecao.delete_one({"_id": ObjectId(agendamento_id)})

    @classmethod
    def editar(cls, agendamento_id, novos_dados):
        return cls.colecao.update_one(
            {"_id": ObjectId(agendamento_id)},
            {"$set": novos_dados}
        )

    @classmethod
    def buscar_proximo(cls, usuario, data_minima):
        return cls.colecao.find_one({
            "usuario": usuario,
            "data": {"$gte": data_minima}
        }, sort=[("data", 1), ("horario", 1)])

    @classmethod
    def contar_por_periodo(cls, data, periodo):
        return cls.colecao.count_documents({
            "data": data,
            "turno": periodo
        })