from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["odontoclin"]
agendamentos = db["agendamentos"]

class Agendamento:
    @staticmethod
    def criar(data):
        agendamentos.insert_one(data)
    @staticmethod
    def buscar_proximo(usuario):
        return agendamentos.find_one({"usuario": usuario}, sort=[('data', 1)])
    @staticmethod
    def cancelar(usuario, data):
        agendamentos.delete_one({"usuario": usuario, "data": data})
    @staticmethod
    def contar_por_periodo(data, periodo):
        """Conta quantos agendamentos existem para determinada data e período"""
        return agendamentos.count_documents({"data": data, "periodo": periodo})