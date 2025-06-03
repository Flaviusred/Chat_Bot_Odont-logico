from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_login
from app.database import db

templates = Jinja2Templates(directory="app/templates")
gestor_router = APIRouter()

# Painel Gestor central
@gestor_router.get("/painel-gestor", response_class=HTMLResponse)
async def painel_gestor(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("painel_gestor.html", {"request": request, "user": user})

# Dashboard
@gestor_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# Agenda (GET: lista e filtro / POST: adiciona agendamento)
@gestor_router.get("/agenda", response_class=HTMLResponse)
async def agenda(request: Request, user=Depends(require_login), 
                 usuario: str = "", data_ini: str = "", data_fim: str = ""):
    ag_collection = db["agendamentos"]
    filtros = {}
    if usuario:
        filtros["usuario"] = usuario
    if data_ini or data_fim:
        filtros["data"] = {}
        if data_ini:
            filtros["data"]["$gte"] = data_ini
        if data_fim:
            filtros["data"]["$lte"] = data_fim
    agendamentos = list(ag_collection.find(filtros, {"_id": 0}))
    return templates.TemplateResponse("agenda.html", {
        "request": request,
        "user": user,
        "filtros": {"usuario": usuario, "data_ini": data_ini, "data_fim": data_fim},
        "agendamentos": agendamentos
    })

@gestor_router.post("/agenda/adicionar")
async def agenda_adicionar(request: Request, user=Depends(require_login),
                           usuario: str = Form(...),
                           tipo: str = Form(...),
                           horario: str = Form(...),
                           periodo: str = Form(...)):
    ag_collection = db["agendamentos"]
    from datetime import datetime
    ag_collection.insert_one({
        "usuario": usuario,
        "tipo": tipo,
        "data": horario,
        "periodo": periodo,
        "cadastrado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.post("/agenda/cancelar")
async def agenda_cancelar(request: Request, user=Depends(require_login),
                          agendamento_id: str = Form(...)):
    ag_collection = db["agendamentos"]
    ag_collection.delete_one({"id": agendamento_id})
    return RedirectResponse("/agenda", status_code=303)

@gestor_router.get("/agenda/editar/{agendamento_id}", response_class=HTMLResponse)
async def agenda_editar_get(request: Request, user=Depends(require_login), agendamento_id: str = ""):
    ag_collection = db["agendamentos"]
    agendamento = ag_collection.find_one({"id": agendamento_id}, {"_id": 0})
    return templates.TemplateResponse("editar_agendamento.html", {
        "request": request,
        "user": user,
        "agendamento": agendamento
    })

@gestor_router.post("/agenda/editar/{agendamento_id}")
async def agenda_editar_post(request: Request, agendamento_id: str, user=Depends(require_login),
                             usuario: str = Form(...),
                             tipo: str = Form(...),
                             data: str = Form(...),
                             periodo: str = Form(...)):
    ...
    ag_collection = db["agendamentos"]
    ag_collection.update_one({"id": agendamento_id}, {"$set": {
        "usuario": usuario,
        "tipo": tipo,
        "data": data,
        "periodo": periodo
    }})
    return RedirectResponse("/agenda", status_code=303)

# Conversas WhatsApp
@gestor_router.get("/conversas", response_class=HTMLResponse)
async def conversas(request: Request, user=Depends(require_login), usuario: str = ""):
    conv_collection = db["conversas"]
    # Se usuario não informado, mostra lista (você pode adaptar para mostrar todos por padrão)
    conversas = []
    if usuario:
        conversas = list(conv_collection.find({"usuario": usuario}, {"_id": 0}))
    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "user": user,
        "usuario": usuario,
        "conversas": conversas
    })

@gestor_router.post("/conversa/{usuario}/responder")
async def responder_conversa(request: Request, usuario: str, user=Depends(require_login), mensagem: str = Form(...)):
    conv_collection = db["conversas"]
    from datetime import datetime
    conv_collection.insert_one({
        "usuario": usuario,
        "mensagem": mensagem,
        "resposta": "Resposta do admin: " + mensagem,
        "momento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return RedirectResponse(f"/conversas?usuario={usuario}", status_code=303)

@gestor_router.post("/conversa/{usuario}/finalizar")
async def finalizar_conversa(request: Request, usuario: str, user=Depends(require_login), mensagem: str = Form(...)):
    # Aqui você pode marcar como finalizada ou remover, conforme sua lógica
    return RedirectResponse("/conversas", status_code=303)