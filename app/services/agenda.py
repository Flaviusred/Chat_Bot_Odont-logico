from app.models.agendamento import AgendamentoModel
from datetime import datetime

TIPOS_ATENDIMENTO = [
    "Consulta",
    "Limpeza",
    "Clareamento",
    "Canal",
    "Extração"
]

HORARIOS_MANHA = ["08:00", "09:00", "10:00", "11:00"]
HORARIOS_TARDE = ["14:00", "15:00", "16:00", "17:00"]

contextos = {}

def parse_data_iso(data):
    try:
        return datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return data

def dia_semana(data_str):
    return datetime.strptime(data_str, "%d/%m/%Y").weekday()

def horarios_ocupados(data, turno):
    data_iso = parse_data_iso(data)
    ags = AgendamentoModel.listar({"data": data_iso, "turno": turno})
    return [a.get("horario") for a in ags if "horario" in a]

def horarios_disponiveis(data, turno):
    todos = HORARIOS_MANHA if turno == "manha" else HORARIOS_TARDE
    ocupados = horarios_ocupados(data, turno)
    return [h for h in todos if h not in ocupados]

def gerar_menu():
    opcoes = "\n".join([f"{i+1}. {tipo}" for i, tipo in enumerate(TIPOS_ATENDIMENTO)])
    return (
        "Olá! 👋 Bem-vindo à Clínica Odontológica.\n"
        "Como posso ajudar?\n"
        "1️⃣ Agendar atendimento\n"
        "2️⃣ Cancelar agendamento\n"
        "3️⃣ Verificar meu agendamento\n"
        "4️⃣ Falar com o atendimento\n\n"
        "Ou escolha um serviço:\n"
        f"{opcoes}\n"
        "*Responda com o número da opção desejada.*"
    )

def fluxo_agendamento(usuario, msg):
    if usuario not in contextos or contextos[usuario].get("etapa") is None:
        contextos[usuario] = {"etapa": "nome", "dados": {}}
        return "Para iniciarmos o agendamento, por favor informe seu nome completo:"

    ctx = contextos[usuario]
    dados = ctx["dados"]

    if ctx["etapa"] == "nome":
        dados["nome"] = msg.strip()
        ctx["etapa"] = "idade"
        return "Qual sua idade?"

    if ctx["etapa"] == "idade":
        if not msg.isdigit() or int(msg) < 0:
            return "Por favor, informe a idade em números."
        dados["idade"] = msg.strip()
        ctx["etapa"] = "telefone"
        return "Qual seu telefone para contato?"

    if ctx["etapa"] == "telefone":
        telefone = ''.join(filter(str.isdigit, msg))
        if len(telefone) < 10:
            return "Por favor, informe um telefone válido (com DDD)."
        dados["telefone"] = telefone
        ctx["etapa"] = "tipo"
        opcoes = "\n".join(f"{i+1}. {tipo}" for i, tipo in enumerate(TIPOS_ATENDIMENTO))
        return (
            "Qual atendimento deseja agendar?\n" +
            opcoes +
            "\n*Responda apenas com o número do atendimento.*"
        )

    if ctx["etapa"] == "tipo":
        try:
            idx = int(msg.strip()) - 1
            if 0 <= idx < len(TIPOS_ATENDIMENTO):
                dados["tipo"] = TIPOS_ATENDIMENTO[idx]
                ctx["etapa"] = "data"
                return "Para qual data deseja agendar? (formato: DD/MM/AAAA)"
            else:
                return "Opção inválida. Escolha uma das opções acima."
        except:
            return "Por favor, responda apenas com o número do atendimento desejado."

    if ctx["etapa"] == "data":
        try:
            datetime.strptime(msg.strip(), "%d/%m/%Y")
            dados["data"] = msg.strip()
        except Exception:
            return "Por favor, informe a data no formato DD/MM/AAAA."
        dsemana = dia_semana(dados["data"])
        if dsemana == 6:  # domingo
            return "O consultório não funciona aos domingos. Por favor, escolha outro dia."
        ctx["etapa"] = "turno"
        if dsemana == 5:
            return "Sábado só temos turno da manhã (08:00-12:00).\nResponda 1 para manhã."
        else:
            return "Qual turno?\n1. Manhã (08:00-12:00)\n2. Tarde (14:00-18:00)\n*Responda 1 ou 2.*"

    if ctx["etapa"] == "turno":
        dsemana = dia_semana(dados["data"])
        if dsemana == 5 and msg.strip() != "1":
            return "Sábado só temos turno da manhã. Por favor, escolha 1."
        if msg.strip() == "1":
            turno = "manha"
        elif msg.strip() == "2":
            turno = "tarde"
        else:
            return "Escolha 1 para Manhã ou 2 para Tarde."
        dados["turno"] = turno
        disponiveis = horarios_disponiveis(dados["data"], turno)
        if not disponiveis:
            ctx["etapa"] = "data"
            return "Nenhum horário disponível nesse turno. Escolha outra data."
        horarios_msg = "\n".join(f"{i+1}. {h}" for i, h in enumerate(disponiveis))
        ctx["etapa"] = "horario"
        dados["horarios_disponiveis"] = disponiveis
        return f"Escolha o horário:\n{horarios_msg}\nResponda o número do horário desejado."

    if ctx["etapa"] == "horario":
        try:
            idx = int(msg.strip()) - 1
            horario = dados["horarios_disponiveis"][idx]
        except Exception:
            return "Escolha inválida. Digite o número do horário desejado."
        # Checa conflito de novo
        if horario in horarios_ocupados(dados["data"], dados["turno"]):
            return "Esse horário acabou de ser reservado. Escolha outro horário."
        dados["horario"] = horario
        ctx["etapa"] = "tipo_atendimento"
        return "O atendimento será por convênio ou particular?"

    if ctx["etapa"] == "tipo_atendimento":
        if msg.lower() in ["convenio", "convênio"]:
            ctx["etapa"] = "convenio_nome"
            return "Qual o nome do convênio?"
        elif msg.lower() == "particular":
            del contextos[usuario]
            return "Vou te direcionar para um atendente humano. Aguarde um momento."
        else:
            return "Por favor, responda 'convênio' ou 'particular'."

    if ctx["etapa"] == "convenio_nome":
        dados["convenio"] = msg.strip()
        # Salva agendamento
        ag = {
            "usuario": usuario,
            "nome": dados["nome"],
            "idade": dados["idade"],
            "telefone": dados["telefone"],
            "tipo": dados["tipo"],
            "data": parse_data_iso(dados["data"]),
            "turno": dados["turno"],
            "horario": dados["horario"],
            "convenio": dados["convenio"],
            "cadastrado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        AgendamentoModel.criar(ag)
        del contextos[usuario]
        return (
            f"✅ Agendamento realizado!\n"
            f"Nome: {ag['nome']}\nTelefone: {ag['telefone']}\n"
            f"Idade: {ag['idade']}\n"
            f"Tipo: {ag['tipo']}\n"
            f"Data: {dados['data']} {ag['horario']} ({'Manhã' if ag['turno']=='manha' else 'Tarde'})\n"
            f"Convênio: {ag['convenio']}\n\n"
            f"Deseja terminar o atendimento ou iniciar uma nova conversa?\n"
            f"Responda 'menu' para iniciar nova conversa ou 'sair' para encerrar."
        )

    del contextos[usuario]
    return "Fluxo perdido. Envie 'menu' para começar novamente."

def fluxo_cancelamento(usuario, msg):
    now = datetime.now().strftime("%Y-%m-%d")
    ags = AgendamentoModel.listar({"usuario": usuario, "data": {"$gte": now}})
    if not ags:
        return "Você não possui agendamentos futuros para cancelar."
    if usuario not in contextos or "cancelar_lista" not in contextos[usuario]:
        contextos[usuario] = {"etapa": "cancelar", "cancelar_lista": ags}
        resposta = "Seus agendamentos futuros:\n"
        for idx, ag in enumerate(ags):
            resposta += f"{idx+1}. {ag.get('tipo','?')} em {ag.get('data','?')} ({ag.get('turno','?')} - {ag.get('horario','?')})\n"
        resposta += "Envie o número do agendamento que deseja cancelar."
        return resposta
    else:
        try:
            idx = int(msg.strip()) - 1
            ags = contextos[usuario]["cancelar_lista"]
            if 0 <= idx < len(ags):
                _id = str(ags[idx]["_id"])
                AgendamentoModel.cancelar(_id)
                del contextos[usuario]
                return "✅ Agendamento cancelado com sucesso."
            else:
                return "Opção inválida. Envie o número correspondente ao agendamento."
        except:
            return "Por favor, envie apenas o número do agendamento para cancelar."

def fluxo_verificacao(usuario):
    now = datetime.now().strftime("%Y-%m-%d")
    ags = AgendamentoModel.listar({"usuario": usuario, "data": {"$gte": now}})
    if ags:
        ag = ags[0]
        return (
            f"Seu próximo agendamento:\n"
            f"Nome: {ag.get('nome','')}\n"
            f"Tipo: {ag.get('tipo','')}\n"
            f"Data: {ag['data']} {ag.get('horario','')} ({'Manhã' if ag['turno']=='manha' else 'Tarde'})\n"
            f"Convênio: {ag.get('convenio','')}"
        )
    return "Você não possui agendamentos futuros."