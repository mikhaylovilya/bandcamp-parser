# bandcamp-parser

Single-page web app that parses Bandcamp release pages (albums/tracks) and stores reports.

Stack: Flask + flasgger (Swagger) backend, Svelte frontend, SQLite.

## Run with docker compose

```bash
docker compose up --build
```

Frontend: http://localhost:8080
Backend API: http://localhost:5000/api
Swagger UI: http://localhost:5000/swagger-ui

## API

- `POST /api/parse` body `{ "url": "https://..." }` -> parsed release + saves report
- `GET /api/reports` -> list saved reports
- `DELETE /api/reports/{id}` -> delete report

## Development

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Frontend:
```bash
cd frontend
npm install
npm run test
npm run dev
```
