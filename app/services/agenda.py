from app.database import db
from datetime import datetime
from bson import ObjectId

LIMITE_POR_PERIODO = 5
TIPOS_ATENDIMENTO = [
    "Consulta",
    "Limpeza",
    "Clareamento",
    "Canal",
    "Extração"
]

class Agendamento:
    @staticmethod
    def criar(dados):
        try:
            data_iso = datetime.strptime(dados["data"], "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            data_iso = dados["data"]
        ag = {
            "usuario": dados["usuario"],
            "tipo": dados["tipo"],
            "data": data_iso,
            "periodo": dados["periodo"],
            "cadastrado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        db.agendamentos.insert_one(ag)

    @staticmethod
    def contar_por_periodo(data, periodo):
        try:
            data_iso = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            data_iso = data
        return db.agendamentos.count_documents({
            "data": data_iso,
            "periodo": periodo
        })

    @staticmethod
    def buscar_proximo(usuario):
        now = datetime.now().strftime("%Y-%m-%d")
        ag = db.agendamentos.find_one(
            {
                "usuario": usuario,
                "data": {"$gte": now}
            },
            sort=[("data", 1)]
        )
        if ag:
            ag["id"] = str(ag["_id"])
        return ag

    @staticmethod
    def listar_agendamentos(usuario=None, data_ini=None, data_fim=None):
        filtro = {}
        if usuario:
            filtro["usuario"] = {"$regex": usuario, "$options": "i"}
        if data_ini or data_fim:
            filtro["data"] = {}
            if data_ini:
                filtro["data"]["$gte"] = data_ini
            if data_fim:
                filtro["data"]["$lte"] = data_fim
            if not filtro["data"]:
                del filtro["data"]
        ags = list(db.agendamentos.find(filtro).sort("data", 1))
        for a in ags:
            a["id"] = str(a["_id"])
        return ags

    @staticmethod
    def cancelar(agendamento_id):
        db.agendamentos.delete_one({"_id": ObjectId(agendamento_id)})

    @staticmethod
    def editar(agendamento_id, usuario, data, periodo, tipo):
        try:
            data_iso = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            data_iso = data
        db.agendamentos.update_one(
            {"_id": ObjectId(agendamento_id)},
            {"$set": {
                "usuario": usuario,
                "data": data_iso,
                "periodo": periodo,
                "tipo": tipo
            }}
        )

    @staticmethod
    def obter(agendamento_id):
        a = db.agendamentos.find_one({"_id": ObjectId(agendamento_id)})
        if a:
            a["id"] = str(a["_id"])
        return a

# Fluxos interativos WhatsApp

contextos = {}

def gerar_menu():
    opcoes = "\n".join([f"{i+1}. {tipo}" for i, tipo in enumerate(TIPOS_ATENDIMENTO)])
    return (
        "Olá! 👋 Bem-vindo à Clínica Odontológica.\n"
        "Como posso ajudar?\n"
        "1️⃣ Agendar atendimento\n"
        "2️⃣ Cancelar agendamento\n"
        "3️⃣ Verificar meu agendamento\n\n"
        "Ou escolha um serviço:\n"
        f"{opcoes}\n"
        "*Responda com o número da opção desejada.*"
    )

def detectar_fluxo(msg):
    if not msg:
        return "ia", {}
    msg_lower = msg.lower()
    if "agendar" in msg_lower or msg_lower == "1":
        return "agendamento", {}
    if "cancelar" in msg_lower or msg_lower == "2":
        return "cancelamento", {}
    if "meu agendamento" in msg_lower or "verificar agendamento" in msg_lower or msg_lower == "3":
        return "verificacao", {}
    return "ia", {}

def fluxo_agendamento(usuario, msg):
    if usuario not in contextos:
        contextos[usuario] = {"etapa": 0}
    ctx = contextos[usuario]

    if ctx["etapa"] == 0:
        ctx["etapa"] = 1
        opcoes = "\n".join(f"{i+1}. {tipo}" for i, tipo in enumerate(TIPOS_ATENDIMENTO))
        return (
            "Qual atendimento deseja agendar?\n" +
            opcoes +
            "\n*Responda apenas com o número do atendimento.*"
        )

    if ctx["etapa"] == 1:
        try:
            idx = int(msg.strip()) - 1
            if 0 <= idx < len(TIPOS_ATENDIMENTO):
                ctx["tipo"] = TIPOS_ATENDIMENTO[idx]
                ctx["etapa"] = 2
                return "Para qual data deseja agendar? (formato: DD/MM/AAAA)"
            else:
                return "Opção inválida. Escolha uma das opções acima."
        except:
            return "Por favor, responda apenas com o número do atendimento desejado."

    if ctx["etapa"] == 2:
        # Validação simples de data
        try:
            datetime.strptime(msg.strip(), "%d/%m/%Y")
        except Exception:
            return "Por favor, informe a data no formato DD/MM/AAAA."
        ctx["data"] = msg.strip()
        ctx["etapa"] = 3
        return "Qual período você prefere?\n1. Manhã\n2. Tarde\n*Responda 1 ou 2.*"

    if ctx["etapa"] == 3:
        periodo = None
        if msg.strip() == "1":
            periodo = "manhã"
        elif msg.strip() == "2":
            periodo = "tarde"
        else:
            return "Escolha 1 para Manhã ou 2 para Tarde."
        ctx["periodo"] = periodo
        qtd = Agendamento.contar_por_periodo(ctx["data"], periodo)
        if qtd >= LIMITE_POR_PERIODO:
            return (
                f"O período {periodo} em {ctx['data']} está cheio. "
                "Deseja tentar outra data ou período? (Envie nova data ou 1/2 para período)"
            )
        Agendamento.criar({
            "usuario": usuario,
            "tipo": ctx["tipo"],
            "data": ctx["data"],
            "periodo": periodo
        })
        del contextos[usuario]
        return (
            f"✅ Agendamento realizado!\n"
            f"Atendimento: {ctx['tipo']}\n"
            f"Data: {ctx['data']}\n"
            f"Período: {periodo.capitalize()}"
        )
    contextos[usuario] = {"etapa": 0}
    opcoes = "\n".join(f"{i+1}. {tipo}" for i, tipo in enumerate(TIPOS_ATENDIMENTO))
    return "Vamos recomeçar. Qual atendimento deseja?\n" + opcoes

def fluxo_cancelamento(usuario, msg):
    # Busca agendamentos futuros
    now = datetime.now().strftime("%Y-%m-%d")
    ags = list(db.agendamentos.find({"usuario": usuario, "data": {"$gte": now}}).sort("data", 1))
    if not ags:
        return "Você não possui agendamentos futuros para cancelar."
    if usuario not in contextos or "cancelar_lista" not in contextos[usuario]:
        contextos[usuario] = {"etapa": "cancelar", "cancelar_lista": ags}
        resposta = "Seus agendamentos futuros:\n"
        for idx, ag in enumerate(ags):
            resposta += f"{idx+1}. {ag['tipo']} em {ag['data']} ({ag['periodo']})\n"
        resposta += "Envie o número do agendamento que deseja cancelar."
        return resposta
    else:
        try:
            idx = int(msg.strip()) - 1
            ags = contextos[usuario]["cancelar_lista"]
            if 0 <= idx < len(ags):
                _id = ags[idx]["_id"]
                db.agendamentos.delete_one({"_id": _id})
                del contextos[usuario]
                return "✅ Agendamento cancelado com sucesso."
            else:
                return "Opção inválida. Envie o número correspondente ao agendamento."
        except:
            return "Por favor, envie apenas o número do agendamento para cancelar."

def fluxo_verificacao(usuario):
    agendamento = Agendamento.buscar_proximo(usuario)
    if agendamento:
        return (
            f"Seu próximo agendamento:\n"
            f"Tipo: {agendamento.get('tipo','')}\n"
            f"Data: {agendamento['data']} ({agendamento['periodo']})"
        )
    return "Você não possui agendamentos futuros."