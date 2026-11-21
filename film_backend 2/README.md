# Backend — подбор фильмов

Бэкенд соответствует теме проекта из корневого README: подбор фильмов по жанру, рейтингу, актёрам, запросу на естественном языке и поиск похожих фильмов.

## Структура

```text
backend/
├── app/
│   ├── main.py                 # FastAPI и CORS
│   ├── schemas.py              # Pydantic-модели Film / Ask
│   ├── api/routes.py            # HTTP-эндпоинты
│   └── services/
│       ├── parser.py            # Загрузка Markdown-карточек фильмов
│       ├── graph.py             # Граф «фильм—жанр—актёр»
│       ├── search.py             # Поиск и похожие фильмы
│       └── rag.py                # Подбор по текстовому запросу, опциональный LLM
├── films/                       # Markdown-каталог
├── requirements.txt
└── .env.example
```

## Установка и запуск

Из папки `backend`:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Проверка: `http://localhost:8000/health`, документация Swagger: `http://localhost:8000/docs`.

## Эндпоинты

- `GET /api/films` — весь каталог.
- `GET /api/films?genre=фантастика&min_rating=8` — фильтрация по жанру, минимальному рейтингу, актёру (`actor`) и году (`year_from`).
- `GET /api/films/{film_id}` — карточка фильма.
- `GET /api/films/{film_id}/similar` — похожие фильмы по заданным связям и общим жанрам/актёрам.
- `POST /api/ask` — подбор по текстовому запросу. Тело: `{"query":"Посоветуй фантастику с рейтингом выше 8"}`.
- `GET /health` — проверка состояния.

Временно оставлены скрытые совместимые адреса `/api/recipes` и `/api/recipes/{id}` на случай, если в текущем React-коде остались старые имена функций.

## OpenAI (необязательно)

Локальный подбор работает и без ключа. Чтобы включить генерацию пояснительного ответа, скопируйте `.env.example` в `.env` и добавьте `OPENAI_API_KEY`. Файл `.env` не следует загружать в GitHub.

Каталог фильмов хранится в `films/*.md`. После добавления/изменения карточек перезапустите сервер.
