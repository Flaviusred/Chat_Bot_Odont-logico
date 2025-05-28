# Painel Gestor Odontológico – WhatsApp Bot e Dashboard

## Sobre

Este projeto integra um chatbot para WhatsApp (Twilio), assistente IA (OpenAI), painel gestor web (FastAPI/Jinja2), e gerenciamento de agendamentos para clínica odontológica.

## Pré-requisitos

- Python 3.10+
- MongoDB em execução (`MONGO_URI`)
- Conta Twilio (WhatsApp)
- Conta OpenAI (API Key)
- Docker (opcional)

## Instalação

1. Clone o projeto e acesse a pasta.
2. Copie o `.env.example` para `.env` e preencha com suas chaves.
3. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute o servidor:
   ```bash
   uvicorn app.main:app --reload
   ```
5. (Opcional) Execute com Docker:
   ```bash
   docker build -t painel-gestor .
   docker run -p 8000:8000 --env-file .env painel-gestor
   ```

## Estrutura

- `app/main.py` – Inicialização FastAPI + webhook Twilio
- `app/gestor_routes.py` – Rotas painel web
- `app/api_routes.py` – Webhook WhatsApp API
- `app/models/` – Models MongoDB (CRUD)
- `app/services/` – Regras de negócio
- `app/templates/` – Templates Jinja2 (HTML)
- `app/static/` – CSS
- `Dockerfile` – Build container
- `.env` – Exemplo de variáveis ambiente

## Fluxo principal

- Usuário interage via WhatsApp
- Fluxos de agendamento/cancelamento/verificação guiados por contexto
- Painel web para gestão, edição e visualização

## Observações

- Não envie `.env` para repositórios públicos!
- Para produção, utilize cache (Redis) para contexto ao invés de dicionário em memória.
- Ajuste o nome do banco se desejar, atualmente `gestor_db`.

---