from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import try_login, create_session, COOKIE_NAME, require_login
from app.services import gestor, humano
from app.services.whatsapp import enviar_mensagem

templates = Jinja2Templates(directory="app/templates")
gestor_router = APIRouter()

@gestor_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@gestor_router.post("/login", response_class=HTMLResponse)
def do_login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if try_login(username, password):
        session = create_session(username)
        resp = RedirectResponse(url="/dashboard", status_code=302)
        resp.set_cookie(key=COOKIE_NAME, value=session, httponly=True)
        return resp
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário/senha inválidos"})

@gestor_router.get("/logout")
def do_logout(response: Response):
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp

@gestor_router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(require_login)):
    atendimentos = humano.listar_atendimentos()
    conversas = gestor.listar_conversas()[-10:]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "atendimentos": atendimentos,
        "conversas": conversas,
        "user": user
    })

@gestor_router.get("/conversa/{usuario}", response_class=HTMLResponse)
def conversa_usuario(request: Request, usuario: str, user=Depends(require_login)):
    conversas = [c for c in gestor.listar_conversas() if c["usuario"] == usuario]
    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "usuario": usuario,
        "conversas": conversas,
        "user": user
    })

@gestor_router.post("/conversa/{usuario}/responder")
def responder_usuario(request: Request, usuario: str, mensagem: str = Form(...), user=Depends(require_login)):
    enviar_mensagem(usuario, mensagem)
    gestor.registrar_conversa(usuario, f"Gestor: {mensagem}", mensagem)
    return RedirectResponse(f"/conversa/{usuario}", status_code=302)

@gestor_router.post("/conversa/{usuario}/finalizar")
def finalizar_usuario(usuario: str, user=Depends(require_login)):
    humano.finalizar_atendimento(usuario)
    return RedirectResponse("/dashboard", status_code=302)

