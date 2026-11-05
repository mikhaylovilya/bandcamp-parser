# bandcamp-parser

Одностраничное веб-приложение, которое собирает данные с страниц релизов Bandcamp (альбомы/треки) и сохраняет отчёты.

Стек: бэкенд Flask + flask-smorest (Swagger), фронтенд Svelte, база данных SQLite.

## Запуск через docker compose

```bash
docker compose up --build
```

Фронтенд: http://localhost:8080
API бэкенда: http://localhost:5000/api
Swagger UI: http://localhost:5000/swagger-ui

Запросы к Bandcamp ограничены: не чаще одного раза в `BANDCAMP_MIN_INTERVAL` секунд (по умолчанию 2). Состояние лимита общее для воркеров gunicorn.

## API

- `POST /api/parse` body `{ "url": "https://..." }` -> распарсенный релиз + сохранение отчёта
- `GET /api/reports` -> список сохранённых отчётов
- `GET /api/reports/{id}` -> конкретный отчёт
- `DELETE /api/reports/{id}` -> удалить отчёт

## Разработка

Бэкенд:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Фронтенд:

```bash
cd frontend
npm install
npm run test
npm run dev
```