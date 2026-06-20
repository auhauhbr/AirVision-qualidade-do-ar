# AirVision

Dashboard de qualidade do ar com frontend React e backend FastAPI, usando dados da OpenAQ v3.

O frontend segue o HTML de referência do projeto: sidebar com filtros, cards de resumo, série temporal com hover/overlays, heatmap hora x dia da semana, tabela de dias críticos e exportação CSV.

## Stack

- Frontend: React, Vite, Plotly
- Backend: FastAPI, pandas, SQLite cache
- Dados: OpenAQ v3

## Como rodar localmente

### Forma mais simples

Na raiz do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
cd frontend
npm run build
cd ..
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`.

O FastAPI servirá tanto a API quanto o frontend compilado. Quando alterar o frontend, execute `npm run build` novamente.

### Desenvolvimento com atualização automática

Terminal 1, na raiz:

```bash
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

Abra `http://127.0.0.1:5173`.

### Primeira instalação

Se o ambiente ainda não estiver instalado:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

A OpenAQ usa autenticação via header `X-API-Key`. Crie uma chave gratuita e coloque em `.env`:

```env
OPENAQ_API_KEY=sua-chave
```

O `.env` não é enviado ao GitHub.

## GitHub Pages

O workflow `.github/workflows/publicar-pages.yml` publica o frontend automaticamente sempre que a branch `main` recebe um push.

1. Envie o novo commit para o GitHub.
2. Abra o repositório no GitHub.
3. Entre em **Settings > Pages**.
4. Em **Build and deployment > Source**, selecione **GitHub Actions**.
5. Abra a aba **Actions** e acompanhe o workflow **Publicar no GitHub Pages**.

O endereço será:

```text
https://auhauhbr.github.io/AirVision-qualidade-do-ar/
```

O GitHub Pages não executa Python/FastAPI. Por isso, sem um backend público configurado, o site publicado usa dados demonstrativos e deixa isso informado na interface.

Para conectar um backend publicado posteriormente:

1. Abra **Settings > Secrets and variables > Actions > Variables**.
2. Crie a variável `VITE_API_BASE_URL`.
3. Use como valor a URL pública do backend, sem barra no final.

Exemplo:

```text
https://api-airvision.exemplo.com
```

Nunca coloque `OPENAQ_API_KEY` nas variáveis `VITE_*`: qualquer variável Vite fica visível no navegador.

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
