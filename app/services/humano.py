from app.models.atendimento import AtendimentoModel
from app.services.whatsapp import enviar_mensagem

PALAVRAS_CHAVE = ["atendimento humano", "falar com atendente", "humano"]

def checar_pedido_humano(msg):
    if not msg:
        return False
    return any(p in msg.lower() for p in PALAVRAS_CHAVE)

def registrar_pedido(usuario):
    AtendimentoModel.criar({"usuario": usuario, "status": "pendente", "mensagens": []})
    enviar_mensagem(usuario, "Seu pedido de atendimento humano foi registrado. Aguarde o atendente.")

def notificar_gestor(usuario):
    # Exemplo: pode ser um push, email, webhook, etc.
    pass

def em_atendimento_humano(usuario):
    return AtendimentoModel.em_andamento(usuario)

def redirecionar_mensagem(usuario, mensagem):
    AtendimentoModel.registrar_mensagem(usuario, mensagem)
    # Aqui você pode enviar para o painel gestor ou WhatsApp do atendente

def listar_atendimentos():
    return AtendimentoModel.todos_pendentes()

def finalizar_atendimento(usuario):
    AtendimentoModel.finalizar(usuario)
    enviar_mensagem(usuario, "O atendimento humano foi finalizado. Posso ajudar em mais alguma coisa?")