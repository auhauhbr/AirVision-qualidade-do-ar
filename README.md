# AirVision

Dashboard de qualidade do ar com frontend React e backend FastAPI, usando dados da OpenAQ v3.

O frontend segue o HTML de referência do projeto: sidebar com filtros, cards de resumo, série temporal com hover/overlays, heatmap hora x dia da semana, tabela de dias críticos e exportação CSV.

## Stack

- Frontend: React, Vite, Plotly
- Backend: FastAPI, pandas, SQLite cache
- Dados: OpenAQ v3

## Como rodar localmente

### 1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

A OpenAQ atualmente usa autenticação via header `X-API-Key`. Crie uma chave gratuita em `https://explore.openaq.org/register` e coloque em `.env`:

```env
OPENAQ_API_KEY=sua-chave
```

Sem chave, ou se a API recusar a chamada, o backend mantém a tela viva com um conjunto demonstrativo e mostra um aviso no topo.

### 2. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://127.0.0.1:5173`.

### Opção em uma porta só

Depois de instalar o frontend, você também pode gerar o build e deixar o FastAPI servir a interface:

```bash
cd frontend
npm run build
cd ..
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`.

## API local

Endpoint principal:

```http
GET /api/measurements?city=Recife&country=BR&parameter=pm25&days=30
```

O frontend usa exatamente esse padrão. O backend resolve cidade para coordenadas, busca estações próximas na OpenAQ, coleta dados diários por sensor, agrega com pandas, calcula médias móveis, tendência, anomalias, conformidade OMS e devolve JSON pronto para os gráficos.

Outros endpoints:

```http
GET /api/health
GET /api/options
```

## Parâmetros suportados

- `pm25`
- `pm10`
- `no2`
- `o3`
- `co`
- `so2`

## Preparar para o GitHub

Quando quiser subir para o repositório vazio:

```bash
git init
git add .
git commit -m "Initial AirVision dashboard"
git branch -M main
git remote add origin https://github.com/auhauhbr/AirVision-qualidade-do-ar.git
git push -u origin main
```

Não suba o arquivo `.env`. Ele já está protegido pelo `.gitignore`.

## Referências

- OpenAQ API docs: https://docs.openaq.org/
- OpenAQ API key: https://docs.openaq.org/using-the-api/api-key
- OpenAQ rate limits: https://docs.openaq.org/using-the-api/rate-limits
