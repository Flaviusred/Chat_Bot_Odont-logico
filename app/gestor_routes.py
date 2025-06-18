from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_login
from app.models.agendamento import AgendamentoModel
from app.models.conversa import ConversaModel
from datetime import datetime, timedelta
import locale

templates = Jinja2Templates(directory="app/templates")
gestor_router = APIRouter()

# Locale para datas por extenso
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass  # fallback

def formatar_data_extenso(data_str):
    dt = datetime.strptime(data_str, "%Y-%m-%d")
    dia_semana_extenso = dt.strftime("%A")
    dia = dt.day
    mes_extenso = dt.strftime("%B")
    ano = dt.year
    data_extenso = f"{dia_semana_extenso.capitalize()}, {dia} de {mes_extenso} de {ano}"
    return {
        "dia_semana_extenso": dia_semana_extenso.capitalize(),
        "dia": dia,
        "mes_extenso": mes_extenso,
        "ano": ano,
        "data_extenso": data_extenso
    }

def preparar_semana(semana):
    nova_semana = []
    for day in semana:
        info = formatar_data_extenso(day["data"])
        day.update(info)
        nova_semana.append(day)
    return nova_semana

def enrich_agendamentos(agendamentos):
    for ag in agendamentos:
        if ag.get("data"):
            info = formatar_data_extenso(ag["data"])
            ag.update(info)
        usuario = ag.get("usuario")
        data_atual = ag.get("data")
        id_atual = ag.get("_id")
        if usuario and data_atual:
            anteriores = AgendamentoModel.listar({
                "usuario": usuario,
                "data": {"$lt": data_atual},
                "_id": {"$ne": id_atual}
            })
            if anteriores:
                ult = sorted(anteriores, key=lambda x: (x["data"], x.get("horario", "")), reverse=True)[0]
                info_ult = formatar_data_extenso(ult["data"])
                ult.update(info_ult)
                ag["ultimo_agendamento"] = {
                    "data_extenso": ult["data_extenso"],
                    "horario": ult.get("horario", ""),
                    "periodo": ult.get("periodo", ""),
                    "tipo": ult.get("tipo", ""),
                    "status": ult.get("status", "Agendado")
                }
            else:
                ag["ultimo_agendamento"] = None
        else:
            ag["ultimo_agendamento"] = None
    return agendamentos

def get_week_days(ref_date=None):
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    hoje = ref_date or datetime.today()
    start = hoje - timedelta(days=hoje.weekday())
    semana = []
    for i in range(7):
        dia = start + timedelta(days=i)
        semana.append({
            "label": dias_semana[dia.weekday()],
            "data": dia.strftime("%Y-%m-%d")
        })
    return semana

def get_horarios():
    return ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]

def validar_data(data_str):
    try:
        datetime.strptime(data_str, "%Y-%m-%d")
        return True
    except Exception:
        return False

def validar_horario(horario_str):
    try:
        datetime.strptime(horario_str, "%H:%M")
        return True
    except Exception:
        return False

def existe_conflito(usuario, data, horario, agendamento_id=None):
    filtro = {
        "usuario": usuario,
        "data": data,
        "horario": horario,
    }
    if agendamento_id:
        filtro["_id"] = {"$ne": agendamento_id}
    return AgendamentoModel.colecao.count_documents(filtro) > 0

# ------------------- Rotas -------------------

@gestor_router.get("/painel-gestor", response_class=HTMLResponse)
async def painel_gestor(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("painel_gestor.html", {"request": request, "user": user})

@gestor_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# ROTA BUSCAR PACIENTE
@gestor_router.get("/buscar-paciente", response_class=HTMLResponse)
async def buscar_paciente(
    request: Request,
    user=Depends(require_login),
    q: str = Query("", alias="q"),
    page: int = 1,
    per_page: int = 10
):
    filtro = {}
    if q:
        filtro["$or"] = [
            {"nome": {"$regex": q, "$options": "i"}},
            {"usuario": {"$regex": q, "$options": "i"}},
            {"telefone": {"$regex": q, "$options": "i"}},
        ]
    total = AgendamentoModel.colecao.count_documents(filtro)
    pacientes = list(
        AgendamentoModel.colecao.find(filtro)
        .sort([("nome", 1)])
        .skip((page-1)*per_page)
        .limit(per_page)
    )
    for ag in pacientes:
        ag["id"] = str(ag["_id"])
    pages = (total + per_page - 1) // per_page
    return templates.TemplateResponse("buscar_paciente.html", {
        "request": request,
        "user": user,
        "q": q,
        "pacientes": pacientes,
        "page": page,
        "pages": pages,
        "total": total,
        "per_page": per_page,
    })

# ROTA PRINCIPAL AGENDA COM FILTROS, PAGINAÇÃO E AVANÇO/RETROCESSO DE SEMANA
@gestor_router.get("/agenda", response_class=HTMLResponse)
async def agenda(
    request: Request,
    user=Depends(require_login),
    usuario: str = "",
    data_ini: str = "",
    data_fim: str = "",
    tipo: str = "",
    status: str = "",
    convenio: str = "",
    periodo: str = "",
    page: int = 1,
    per_page: int = 15
):
    # Calcula data inicial da semana
    if data_ini:
        try:
            ref_date = datetime.strptime(data_ini, "%Y-%m-%d")
        except Exception:
            ref_date = datetime.today()
    else:
        ref_date = datetime.today()
    semana = get_week_days(ref_date)
    semana = preparar_semana(semana)
    horarios = get_horarios()
    data_inicio = semana[0]["data"]
    data_fim_semana = semana[-1]["data"]

    filtro = {"data": {}}
    if data_ini:
        filtro["data"]["$gte"] = data_ini
    else:
        filtro["data"]["$gte"] = data_inicio
    if data_fim:
        filtro["data"]["$lte"] = data_fim
    else:
        filtro["data"]["$lte"] = data_fim_semana
    if usuario:
        filtro["usuario"] = usuario
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    if convenio:
        filtro["convenio"] = convenio
    if periodo:
        filtro["periodo"] = periodo
    if not filtro["data"]:
        filtro.pop("data")
    total = AgendamentoModel.colecao.count_documents(filtro)
    ags = list(
        AgendamentoModel.colecao.find(filtro)
        .sort([("data", 1), ("horario", 1)])
        .skip((page-1)*per_page)
        .limit(per_page)
    )
    ags = enrich_agendamentos(ags)
    agendamentos_map = {dia["data"]: [] for dia in semana}
    for ag in ags:
        ag["id"] = str(ag["_id"])
        ag["status"] = ag.get("status", "Agendado")
        ag["data"] = ag.get("data", "")
        ag["horario"] = ag.get("horario", "")
        if ag["data"] in agendamentos_map:
            agendamentos_map[ag["data"]].append(ag)

    dia_hoje = datetime.today().strftime("%Y-%m-%d")
    agendamentos_do_dia = [ag for ag in ags if ag.get("data") == dia_hoje]
    agendamentos_do_dia.sort(key=lambda x: x.get("horario", ""))

    ano_atual = datetime.today().year
    pages = (total + per_page - 1) // per_page

    # Para navegação de semana no template Jinja2
    return templates.TemplateResponse("agenda.html", {
        "request": request,
        "user": user,
        "filtros": {"usuario": usuario, "data_ini": data_ini, "data_fim": data_fim,
                    "tipo": tipo, "status": status, "convenio": convenio, "periodo": periodo},
        "semana": semana,
        "horarios": horarios,
        "agendamentos_map": agendamentos_map,
        "agendamentos_do_dia": agendamentos_do_dia,
        "ano_atual": ano_atual,
        "page": page,
        "pages": pages,
        "total": total,
        "per_page": per_page,
        "datetime": datetime,             # <-- Importante para navegação Jinja2
        "timedelta": timedelta            # <-- Importante para navegação Jinja2
    })

@gestor_router.post("/agenda/adicionar")
async def agenda_adicionar(request: Request, user=Depends(require_login),
                           usuario: str = Form(...),
                           nome: str = Form(None),
                           idade: str = Form(None),
                           telefone: str = Form(None),
                           tipo: str = Form(...),
                           data: str = Form(...),
                           periodo: str = Form(...),
                           horario: str = Form(...),
                           convenio: str = Form(None)):
    if not validar_data(data):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Data inválida! Use o formato AAAA-MM-DD."
        }, status_code=400)
    if not validar_horario(horario):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Horário inválido! Use o formato HH:MM."
        }, status_code=400)
    if existe_conflito(usuario, data, horario):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Já existe agendamento para este usuário, data e horário!"
        }, status_code=400)
    agendamento = {
        "usuario": usuario,
        "nome": nome,
        "idade": idade,
        "telefone": telefone,
        "tipo": tipo,
        "data": data,
        "periodo": periodo,
        "horario": horario,
        "convenio": convenio,
        "status": "Agendado",
        "cadastrado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    AgendamentoModel.criar({k: v for k, v in agendamento.items() if v is not None})
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.post("/agenda/cancelar")
async def agenda_cancelar(request: Request, agendamento_id: str = Form(...), user=Depends(require_login)):
    AgendamentoModel.cancelar(agendamento_id)
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.post("/agenda/editar_status/{agendamento_id}")
async def editar_status_agendamento(
    request: Request,
    agendamento_id: str,
    status: str = Form(...),
    user=Depends(require_login)
):
    AgendamentoModel.editar_status(agendamento_id, status)
    return RedirectResponse(request.headers.get("referer", "/agenda"), status_code=303)

@gestor_router.get("/agenda/editar/{agendamento_id}", response_class=HTMLResponse)
async def agenda_editar_get(request: Request, agendamento_id: str, user=Depends(require_login)):
    agendamento = AgendamentoModel.obter(agendamento_id)
    agendamento["id"] = str(agendamento["_id"])
    return templates.TemplateResponse("editar_agendamento.html", {
        "request": request,
        "user": user,
        "agendamento": agendamento
    })

@gestor_router.post("/agenda/editar/{agendamento_id}")
async def agenda_editar_post(request: Request, agendamento_id: str, user=Depends(require_login),
                             usuario: str = Form(...),
                             nome: str = Form(None),
                             idade: str = Form(None),
                             telefone: str = Form(None),
                             tipo: str = Form(...),
                             data: str = Form(...),
                             periodo: str = Form(...),
                             horario: str = Form(...),
                             convenio: str = Form(None)):
    if not validar_data(data):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Data inválida! Use o formato AAAA-MM-DD."
        }, status_code=400)
    if not validar_horario(horario):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Horário inválido! Use o formato HH:MM."
        }, status_code=400)
    if existe_conflito(usuario, data, horario, agendamento_id):
        return templates.TemplateResponse("erro.html", {
            "request": request,
            "mensagem": "Já existe agendamento para este usuário, data e horário!"
        }, status_code=400)
    novos_dados = {
        "usuario": usuario,
        "nome": nome,
        "idade": idade,
        "telefone": telefone,
        "tipo": tipo,
        "data": data,
        "periodo": periodo,
        "horario": horario,
        "convenio": convenio,
    }
    AgendamentoModel.editar(agendamento_id, {k: v for k, v in novos_dados.items() if v is not None})
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.get("/conversas", response_class=HTMLResponse)
async def conversas(request: Request, user=Depends(require_login), usuario: str = ""):
    if usuario:
        conversas = list(ConversaModel.todos())
        conversas = [c for c in conversas if c["usuario"] == usuario]
    else:
        conversas = list(ConversaModel.todos())
    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "user": user,
        "usuario": usuario,
        "conversas": conversas
    })

@gestor_router.post("/conversa/{usuario}/responder")
async def responder_conversa(request: Request, usuario: str, user=Depends(require_login), mensagem: str = Form(...)):
    ConversaModel.criar(usuario, mensagem, f"Resposta do admin: {mensagem}")
    return RedirectResponse(f"/conversas?usuario={usuario}", status_code=303)

@gestor_router.post("/conversa/{usuario}/finalizar")
async def finalizar_conversa(request: Request, usuario: str, user=Depends(require_login)):
    return RedirectResponse("/conversas", status_code=303)