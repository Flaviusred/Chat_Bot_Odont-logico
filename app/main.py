from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from app.gestor_routes import gestor_router
from app.services.whatsapp import enviar_mensagem
from app.services import agenda
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(gestor_router)

contextos = agenda.contextos

@app.post("/webhook")
async def webhook_twilio(request: Request):
    form = await request.form()
    from_number = form.get("From")
    msg_body = form.get("Body", "").strip()
    usuario = from_number

    MENU_OPCOES = agenda.gerar_menu()

    if usuario not in contextos or msg_body.lower() in ["menu", "oi", "olá", "inicio", "start"]:
        contextos[usuario] = {"etapa": "menu"}
        enviar_mensagem(from_number, MENU_OPCOES)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    etapa = contextos[usuario].get("etapa", "menu")

    if etapa == "menu":
        if msg_body == "1":
            contextos[usuario] = {"etapa": 0}
            resposta = agenda.fluxo_agendamento(usuario, "")
        elif msg_body == "2":
            resposta = agenda.fluxo_cancelamento(usuario, "")
        elif msg_body == "3":
            resposta = agenda.fluxo_verificacao(usuario)
        elif msg_body in [str(i+1) for i in range(len(agenda.TIPOS_ATENDIMENTO))]:
            tipo = agenda.TIPOS_ATENDIMENTO[int(msg_body)-1]
            contextos[usuario] = {"etapa": 1, "tipo": tipo}
            resposta = f"Você escolheu: {tipo}\nPara qual data deseja agendar? (formato: DD/MM/AAAA)"
        else:
            resposta = "Por favor, escolha uma opção válida.\n" + MENU_OPCOES
        enviar_mensagem(from_number, resposta)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    if etapa in [0, 1, 2, 3]:
        resposta = agenda.fluxo_agendamento(usuario, msg_body)
        if resposta.startswith("✅ Agendamento realizado!") or resposta.startswith("Vamos recomeçar"):
            enviar_mensagem(from_number, resposta + "\n\n" + MENU_OPCOES)
            contextos[usuario] = {"etapa": "menu"}
        else:
            enviar_mensagem(from_number, resposta)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    if etapa == "cancelar":
        resposta = agenda.fluxo_cancelamento(usuario, msg_body)
        if resposta.startswith("✅ Agendamento cancelado"):
            enviar_mensagem(from_number, resposta + "\n\n" + MENU_OPCOES)
            contextos[usuario] = {"etapa": "menu"}
        else:
            enviar_mensagem(from_number, resposta)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")
    
    enviar_mensagem(from_number, MENU_OPCOES)
    contextos[usuario] = {"etapa": "menu"}
    return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")