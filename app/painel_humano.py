from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_login
from app.services import humano
from app.services.whatsapp import enviar_mensagem

templates = Jinja2Templates(directory="app/templates")
painel_humano_router = APIRouter()

@painel_humano_router.get("/painel-humano", response_class=HTMLResponse)
def painel_humano(request: Request, user=Depends(require_login)):
    pendentes = humano.listar_atendimentos()
    return templates.TemplateResponse("painel_humano.html", {"request": request, "pendentes": pendentes, "user": user})

@painel_humano_router.get("/painel-humano/conversa/{usuario}", response_class=HTMLResponse)
def conversa_usuario(request: Request, usuario: str, user=Depends(require_login)):
    atendimento = humano.em_atendimento_humano(usuario)
    msgs = atendimento["mensagens"] if atendimento else []
    return templates.TemplateResponse("conversa_humano.html", {"request": request, "usuario": usuario, "msgs": msgs, "user": user})

@painel_humano_router.post("/painel-humano/conversa/{usuario}/responder")
def responder_usuario(usuario: str, mensagem: str = Form(...), user=Depends(require_login)):
    humano.redirecionar_mensagem(usuario, f"Atendente: {mensagem}")
    enviar_mensagem(usuario, mensagem)
    return RedirectResponse(f"/painel-humano/conversa/{usuario}", status_code=302)

@painel_humano_router.post("/painel-humano/conversa/{usuario}/finalizar")
def finalizar_usuario(usuario: str, user=Depends(require_login)):
    humano.finalizar_atendimento(usuario)
    return RedirectResponse("/painel-humano", status_code=302)