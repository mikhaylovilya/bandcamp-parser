# Заметки разработчика

## Стек

- Бэкенд: Python 3.12 (Docker) / 3.14 (локально), Flask, flask-smorest (OpenAPI/Swagger), marshmallow, SQLAlchemy, BeautifulSoup4, requests.
- Фронтенд: Svelte 5 + Vite, vitest + @testing-library/svelte.
- БД: SQLite (файл в `/data` в контейнере, `bandcamp.db` локально).
- Инфраструктура: Docker Compose, nginx для SPA + обратный прокси к бэкенду, GitHub Actions CI.

## Архитектура

- `backend/app/parser.py` — чистый HTML-парсер, без сети. `parse_release(html, url)` возвращает словарь с полями и списком `errors`.
- `backend/app/api.py` — Flask blueprint. `fetch_html` — единственное обращение к сети, в тестах мокается.
- `backend/app/ratelimit.py` — пауза между запросами к Bandcamp (`BANDCAMP_MIN_INTERVAL`, по умолчанию 2 с). Метка времени в файле под lock, чтобы воркеры gunicorn делили один лимит на IP. При ответе 429 запрос повторяется один раз, не дольше 30 с.
- `backend/app/models.py` — таблица `Report` хранит URL, заголовок, артиста, тип и полный распарсенный JSON.
- Фронтенд обращается к относительному `/api`, который nginx проксирует к бэкенду в продакшене и Vite — в dev-режиме.

## Точки расширения

- `AudioDownloader` в `parser.py` — заглушка для будущей загрузки аудио. Реализуйте `download(release, destination)` и подключите к API без изменения парсера.
- Парсер намеренно терпимый: отсутствующие поля порождают записи в `errors`, а не исключения.

## Известные ограничения

- Комментарии и тексты песен зависят от статического HTML; динамические секции, подгружаемые JS, не захватываются.
- Дата релиза при отсутствии `release_date` берётся из `publish_date`.
- Валюта берётся из `data-cart`; для некоторых страниц может быть null.
- `frontend/src/lib/Counter.svelte` — остаток шаблона, не используется.