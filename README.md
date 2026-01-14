# Micro-SaaS Treinos via WhatsApp + Google Sheets

Este repositório entrega um MVP de micro-SaaS para registrar treinos via WhatsApp, com persistência em uma planilha Google Sheets MASTER (multi-tenant) e dashboard simples em Static Site no Render.

## Estrutura do projeto

```
backend/
  app/main.py
  app/routers/{api.py, webhook.py}
  app/services/{sheets_service.py, plan_service.py, parse_service.py, navy_bf.py, dashboard_service.py, whatsapp_service.py}
  app/core/{config.py, logging.py, utils.py}
  tests/
frontend/
  index.html
  cadastro.html
  medidas.html
  dashboard.html
  assets/{app.css, app.js}
scripts/
  setup_sheet.py
```

## Pré-requisitos

- Python 3.11+
- Conta no Google Cloud com acesso ao Google Sheets API
- Conta no Meta WhatsApp Cloud API

## Configuração Google Sheets

1. Crie um projeto no Google Cloud e habilite a **Google Sheets API**.
2. Crie uma **Service Account** e baixe o JSON.
3. Crie a planilha MASTER e compartilhe com o e-mail da Service Account com permissão de edição.
4. Salve o JSON localmente (ou exporte via variável de ambiente).

### Variáveis necessárias

Copie `.env.example` para `.env` e preencha:

```
GOOGLE_SHEET_ID=seu_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ... }'
```

Você pode usar `GOOGLE_SERVICE_ACCOUNT_FILE` para apontar para o arquivo JSON.

### Criar abas e cabeçalhos

Execute:

```
python -m scripts.setup_sheet
```

Isso cria todas as abas (Personals, Alunos, PlanSequence, Plano, LogSets, LogResumo, Medidas, RawMessages).

## Configuração WhatsApp Cloud API

1. Crie um app no [Meta for Developers](https://developers.facebook.com/).
2. Ative **WhatsApp Cloud API**.
3. Configure o número de telefone e gere o **token**.
4. Defina o webhook apontando para `https://SEU_BACKEND/webhook/whatsapp`.
5. Configure o **Verify Token** (mesmo valor em `WHATSAPP_VERIFY_TOKEN`).

### Variáveis

```
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
```

## Rodando localmente

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(cat .env | xargs)
uvicorn app.main:app --reload --app-dir backend
```

## Endpoints

- `POST /api/register`
- `POST /api/measurements`
- `GET /api/dashboard?whatsapp_e164=...`
- `GET /webhook/whatsapp` (verificação)
- `POST /webhook/whatsapp` (recebimento de mensagens)

## Fluxo no WhatsApp

### Cadastro
Use o site `cadastro.html` para cadastrar o aluno. O identificador é o WhatsApp em formato E.164.

### Enviar PLANO
Envie via WhatsApp:

```
PLANO
PUSH
Supino inclinado|4|8|sup inclinado,smith inclinado
PULL
Pulldown frente|4|8|pulldown,puxada frente
LEGS 1
Hack squat|4|8|hack
UPPER
Supino máquina|3|10|sup maquina
LEGS 2
Stiff|4|8|stiff
```

### Solicitar TREINO
Envie:

```
TREINO
```

O bot retornará o template da sessão atual e criará uma sessão ativa na aba `LogResumo`.

### Registrar CARGAS
Envie:

```
CARGAS
Supino inclinado: 90/85/80/75
Supino halter: 36/34/32
```

O bot salva sets em `LogSets`, calcula volume estimado e avança o `next_workout_index` apenas uma vez por sessão.

## Medidas e recomposição

Use `medidas.html` para registrar peso e medidas. O backend calcula:
- BF% (US Navy)
- Massa magra estimada

## Dashboard

Abra `dashboard.html` para visualizar:
- Peso ao longo do tempo
- BF% e massa magra
- Volume semanal/mensal
- Consistência (treinos/semana)
- Evolução de carga por exercício
- Strength Index

Se estiver servindo o frontend separado do backend, defina `window.API_BASE` via tag inline ou salve `apiBase` no `localStorage` com a URL do backend.

## Deploy no Render

### Backend (Web Service)
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- Adicione variáveis de ambiente do `.env.example`

### Frontend (Static Site)
- Root Directory: `frontend`
- Publish Directory: `.`

Opcional: use `render.yaml` para deploy automático.

## Testes

```
pytest backend/tests
```
