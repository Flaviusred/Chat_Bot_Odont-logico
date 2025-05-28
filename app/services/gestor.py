from app.models.conversa import ConversaModel

def registrar_conversa(usuario, msg_usuario, resposta_bot):
    ConversaModel.criar(usuario, msg_usuario, resposta_bot)

def listar_conversas():
    return ConversaModel.todos()