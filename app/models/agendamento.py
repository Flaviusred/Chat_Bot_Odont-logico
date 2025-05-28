from app.database import db
from bson import ObjectId

agendamentos = db["agendamentos"]

class AgendamentoModel:
    @staticmethod
    def criar(data):
        return agendamentos.insert_one(data)

    @staticmethod
    def buscar_proximo(usuario, now_iso):
        return agendamentos.find_one(
            {"usuario": usuario, "data": {"$gte": now_iso}},
            sort=[('data', 1)]
        )

    @staticmethod
    def cancelar(_id):
        return agendamentos.delete_one({"_id": ObjectId(_id)})

    @staticmethod
    def contar_por_periodo(data, periodo):
        return agendamentos.count_documents({"data": data, "periodo": periodo})

    @staticmethod
    def listar(filtro=None):
        filtro = filtro or {}
        return list(agendamentos.find(filtro).sort("data", 1))

    @staticmethod
    def editar(_id, update):
        return agendamentos.update_one(
            {"_id": ObjectId(_id)},
            {"$set": update}
        )

    @staticmethod
    def obter(_id):
        return agendamentos.find_one({"_id": ObjectId(_id)})