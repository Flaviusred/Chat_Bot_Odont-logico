import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def enviar_mensagem(to, mensagem):
    # to no formato 'whatsapp:+5511999999999'
    message = client.messages.create(
        from_=f"whatsapp:{TWILIO_NUMBER}",
        body=mensagem,
        to=to
    )
    return message.sid