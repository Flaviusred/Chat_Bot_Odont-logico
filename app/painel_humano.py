from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_login
from app.models.atendimento import AtendimentoModel

templates = Jinja2Templates(directory="app/templates")
painel_humano_router = APIRouter()

@painel_humano_router.get("/painel-humano", response_class=HTMLResponse)
async def painel_humano(request: Request, user=Depends(require_login)):
    pendentes = AtendimentoModel.todos_pendentes()
    return templates.TemplateResponse("painel_humano.html", {"request": request, "user": user, "pendentes": pendentes})

@painel_humano_router.get("/painel-humano/conversa/{usuario}", response_class=HTMLResponse)
async def conversa_humano(request: Request, usuario: str, user=Depends(require_login)):
    atendimento = AtendimentoModel.em_andamento(usuario)
    msgs = atendimento["mensagens"] if atendimento else []
    return templates.TemplateResponse("conversa_humano.html", {"request": request, "user": user, "usuario": usuario, "msgs": msgs})

@painel_humano_router.post("/painel-humano/conversa/{usuario}/responder")
async def responder_humano(request: Request, usuario: str, user=Depends(require_login), mensagem: str = Form(...)):
    AtendimentoModel.registrar_mensagem(usuario, f"Atendente: {mensagem}")
    return RedirectResponse(f"/painel-humano/conversa/{usuario}", status_code=303)

@painel_humano_router.post("/painel-humano/conversa/{usuario}/finalizar")
async def finalizar_humano(request: Request, usuario: str, user=Depends(require_login)):
    AtendimentoModel.finalizar(usuario)
    return RedirectResponse("/painel-humano", status_code=303)