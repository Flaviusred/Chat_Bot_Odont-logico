from app.models.conversa import Conversa

def registrar_conversa(usuario, msg_usuario, resposta_bot):
    Conversa.criar(usuario, msg_usuario, resposta_bot)

def listar_conversas():
    return Conversa.todos()