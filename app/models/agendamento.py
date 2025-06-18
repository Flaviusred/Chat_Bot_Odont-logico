from app.database import db
from bson import ObjectId

agendamentos = db["agendamentos"]

class AgendamentoModel:
    colecao = db["agendamentos"]

    @classmethod
    def criar(cls, dados):
        # Garante que o campo status sempre existe
        if 'status' not in dados or not dados['status']:
            dados['status'] = "Agendado"
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
        # Se o status não vier, não remove o antigo
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
        # Suporte tanto para campo 'periodo' quanto 'turno'
        return cls.colecao.count_documents({
            "data": data,
            "$or": [
                {"periodo": periodo},
                {"turno": periodo}
            ]
        })

    @classmethod
    def listar_semana(cls, data_inicio, data_fim, usuario=None):
        """Lista agendamentos de uma semana, agrupando por data."""
        filtro = {"data": {"$gte": data_inicio, "$lte": data_fim}}
        if usuario:
            filtro["usuario"] = usuario
        ags = list(cls.colecao.find(filtro))
        # Garante que todo agendamento tenha status preenchido
        for ag in ags:
            if "status" not in ag or not ag["status"]:
                ag["status"] = "Agendado"
        return ags

    @classmethod
    def listar_do_dia(cls, data):
        """Lista e ordena agendamentos do dia por horário."""
        ags = list(cls.colecao.find({"data": data}))
        ags.sort(key=lambda x: x.get("horario", ""))
        for ag in ags:
            if "status" not in ag or not ag["status"]:
                ag["status"] = "Agendado"
        return ags

    @classmethod
    def editar_status(cls, agendamento_id, novo_status):
        return cls.colecao.update_one(
            {"_id": ObjectId(agendamento_id)},
            {"$set": {"status": novo_status}}
        )