import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def chamar_ia(msg):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Atenda como um assistente de consultório odontológico."},
            {"role": "user", "content": msg},
        ],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()