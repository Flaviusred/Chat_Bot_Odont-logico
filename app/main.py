from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from app.auth import auth_router
from app.gestor_routes import gestor_router
from app.painel_humano import painel_humano_router
from app.services.whatsapp import enviar_mensagem
from app.services import agenda, humano
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(gestor_router)
app.include_router(painel_humano_router)
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

    if msg_body.lower() == "sair":
        if usuario in contextos:
            del contextos[usuario]
        enviar_mensagem(from_number, "Atendimento encerrado. Obrigado por utilizar nosso serviço!")
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    etapa = contextos[usuario].get("etapa", "menu")

    if etapa == "menu":
        if msg_body == "1":
            contextos[usuario] = {"etapa": None, "dados": {}}
            resposta = agenda.fluxo_agendamento(usuario, "")
        elif msg_body == "2":
            resposta = agenda.fluxo_cancelamento(usuario, "")
        elif msg_body == "3":
            resposta = agenda.fluxo_verificacao(usuario)
        elif msg_body == "4":
            contextos[usuario] = {"etapa": "humano"}
            humano.registrar_pedido(usuario)
            resposta = "Você será direcionado para o atendimento humano. Aguarde um momento enquanto um atendente assume a conversa. Para voltar ao menu, digite 'menu'."
            enviar_mensagem(from_number, resposta)
            return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")
        elif msg_body in [str(i+1) for i in range(len(agenda.TIPOS_ATENDIMENTO))]:
            tipo = agenda.TIPOS_ATENDIMENTO[int(msg_body)-1]
            contextos[usuario] = {"etapa": "tipo", "dados": {"tipo": tipo}}
            resposta = agenda.fluxo_agendamento(usuario, msg_body)
        else:
            resposta = "Por favor, escolha uma opção válida.\n" + MENU_OPCOES
        enviar_mensagem(from_number, resposta)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    if etapa == "humano":
        if msg_body.lower() == "menu":
            humano.finalizar_atendimento(usuario)
            contextos[usuario] = {"etapa": "menu"}
            enviar_mensagem(from_number, MENU_OPCOES)
        elif msg_body.lower() == "sair":
            humano.finalizar_atendimento(usuario)
            if usuario in contextos:
                del contextos[usuario]
            enviar_mensagem(from_number, "Atendimento encerrado. Obrigado por utilizar nosso serviço!")
        else:
            humano.redirecionar_mensagem(usuario, f"Usuário: {msg_body}")
            enviar_mensagem(from_number, "Você está sendo atendido por um atendente humano. Aguarde resposta. Para voltar ao menu digite 'menu'.")
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    if etapa not in ["menu", "cancelar"]:
        resposta = agenda.fluxo_agendamento(usuario, msg_body)
        if resposta.startswith("✅ Agendamento realizado!"):
            enviar_mensagem(from_number, resposta)
            contextos[usuario] = {"etapa": "aguardando_acao_final"}
        elif resposta.startswith("Vou te direcionar para um atendente humano"):
            contextos[usuario] = {"etapa": "humano"}
            humano.registrar_pedido(usuario)
            enviar_mensagem(from_number, "Você será direcionado para o atendimento humano. Aguarde um momento enquanto um atendente assume a conversa.\nPara voltar ao menu, digite 'menu'.")
        else:
            enviar_mensagem(from_number, resposta)
        return PlainTextResponse("<Response></Response>", status_code=200, media_type="application/xml")

    if etapa == "aguardando_acao_final":
        if msg_body.lower() == "menu":
            contextos[usuario] = {"etapa": "menu"}
            enviar_mensagem(from_number, MENU_OPCOES)
        elif msg_body.lower() == "sair":
            del contextos[usuario]
            enviar_mensagem(from_number, "Atendimento encerrado. Obrigado por utilizar nosso serviço!")
        else:
            enviar_mensagem(from_number, "Deseja terminar o atendimento ou iniciar uma nova conversa?\nResponda 'menu' para nova conversa ou 'sair' para encerrar.")
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