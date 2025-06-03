from app.models.atendimento import AtendimentoModel
from app.services.whatsapp import enviar_mensagem

PALAVRAS_CHAVE = ["atendimento humano", "falar com atendente", "humano"]

def listar_atendimentos():
    return AtendimentoModel.todos_pendentes()

def registrar_pedido(usuario):
    AtendimentoModel.criar({"usuario": usuario})
    enviar_mensagem(usuario, "Seu pedido de atendimento humano foi registrado. Aguarde o atendente.")

def em_atendimento_humano(usuario):
    return AtendimentoModel.em_andamento(usuario)

def redirecionar_mensagem(usuario, mensagem):
    AtendimentoModel.registrar_mensagem(usuario, mensagem)

def notificar_gestor(usuario):
    # Exemplo: pode ser um push, email, webhook, etc.
    pass

def finalizar_atendimento(usuario):
    AtendimentoModel.finalizar(usuario)
    enviar_mensagem(usuario, "O atendimento humano foi finalizado. Posso ajudar em mais alguma coisa?")