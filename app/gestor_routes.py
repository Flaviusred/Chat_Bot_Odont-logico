from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_login
from app.models.agendamento import AgendamentoModel
from app.models.conversa import ConversaModel
from datetime import datetime

templates = Jinja2Templates(directory="app/templates")
gestor_router = APIRouter()

@gestor_router.get("/painel-gestor", response_class=HTMLResponse)
async def painel_gestor(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("painel_gestor.html", {"request": request, "user": user})

@gestor_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@gestor_router.get("/agenda", response_class=HTMLResponse)
async def agenda(request: Request, user=Depends(require_login), 
                 usuario: str = "", data_ini: str = "", data_fim: str = ""):
    filtros = {}
    if usuario:
        filtros["usuario"] = usuario
    if data_ini or data_fim:
        filtros["data"] = {}
        if data_ini:
            filtros["data"]["$gte"] = data_ini
        if data_fim:
            filtros["data"]["$lte"] = data_fim
    agendamentos = AgendamentoModel.listar(filtros)
    for ag in agendamentos:
        ag["id"] = str(ag["_id"])
    return templates.TemplateResponse("agenda.html", {
        "request": request,
        "user": user,
        "filtros": {"usuario": usuario, "data_ini": data_ini, "data_fim": data_fim},
        "agendamentos": agendamentos
    })

@gestor_router.post("/agenda/adicionar")
async def agenda_adicionar(request: Request, user=Depends(require_login),
                           usuario: str = Form(...),
                           nome: str = Form(None),
                           idade: str = Form(None),
                           telefone: str = Form(None),
                           tipo: str = Form(...),
                           horario: str = Form(...),
                           periodo: str = Form(...),
                           convenio: str = Form(None)):
    # Adiciona todos os campos possíveis
    agendamento = {
        "usuario": usuario,
        "nome": nome,
        "idade": idade,
        "telefone": telefone,
        "tipo": tipo,
        "data": horario,
        "periodo": periodo,
        "convenio": convenio,
        "cadastrado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    AgendamentoModel.criar({k: v for k, v in agendamento.items() if v is not None})
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.post("/agenda/cancelar")
async def agenda_cancelar(request: Request, agendamento_id: str = Form(...), user=Depends(require_login)):
    AgendamentoModel.cancelar(agendamento_id)
    return RedirectResponse("/agenda", status_code=303)

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
                             convenio: str = Form(None)):
    novos_dados = {
        "usuario": usuario,
        "nome": nome,
        "idade": idade,
        "telefone": telefone,
        "tipo": tipo,
        "data": data,
        "periodo": periodo,
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
    # Lógica para finalizar conversa, se necessário
    return RedirectResponse("/conversas", status_code=303)