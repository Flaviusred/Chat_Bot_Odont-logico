from fastapi import APIRouter, Request
from app.services import whatsapp, agenda, ia, gestor, humano

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    user_msg = data.get("message")
    user_number = data.get("from")

    if humano.em_atendimento_humano(user_number):
        humano.redirecionar_mensagem(user_number, user_msg)
        return {"status": "ok"}

    if humano.checar_pedido_humano(user_msg):
        humano.registrar_pedido(user_number)
        humano.notificar_gestor(user_number)
        return {"status": "ok"}

    tipo_fluxo, _ = agenda.detectar_fluxo(user_msg)
    if tipo_fluxo == "agendamento":
        resposta = agenda.fluxo_agendamento(user_number, user_msg)
    elif tipo_fluxo == "cancelamento":
        resposta = agenda.fluxo_cancelamento(user_number, user_msg)
    elif tipo_fluxo == "verificacao":
        resposta = agenda.fluxo_verificacao(user_number)
    else:
        resposta = ia.chamar_ia(user_msg)

    gestor.registrar_conversa(user_number, user_msg, resposta)
    whatsapp.enviar_mensagem(user_number, resposta)
    return {"status": "ok"}