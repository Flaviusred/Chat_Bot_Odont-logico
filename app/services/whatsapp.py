import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("AC42afb1dae4881d3f253d5b75fb277252")
TWILIO_AUTH_TOKEN = os.getenv("40fe8f1e6ae5a52fa35a9a947f02fb91")
TWILIO_NUMBER = os.getenv("whatsapp:+14155238886")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def enviar_mensagem(numero, mensagem):
    # numero no formato 'whatsapp:+5511999999999'
    message = client.messages.create(
        from_=f"whatsapp:{TWILIO_NUMBER}",
        body=mensagem,
        to='whatsapp:+558386800849'
    )
    return message.sid