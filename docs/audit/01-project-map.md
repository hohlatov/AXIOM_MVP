# 01 — Карта репозитория и стека (Фаза 1)

> Аудит проведён: 2026-09-11. Источник — прямое чтение кода в `C:\axiom\axiom_project` (коммит `47ef249`, ветка `main`, есть незакоммиченные файлы — см. раздел «Git-статус»).

## Git-статус на начало аудита

Ветка `main`, синхронизирована с `origin/main`. Незакоммичено:
- `.claude/`, `AXIOM_AUDIT.md`, `CLAUDE.md` — служебные файлы для этого аудита.
- `Задание 2. Подготовка Custdev.xlsx`, `Паспорт проекта AXIOM (трек «Стартап» 2025).xlsx`, `Питч-дек AXIOM.pptx` — бизнес-документация трека «Стартап», лежит в корне репозитория, не в `docs/`.

Последние 10 коммитов — почти все про деплой (`Bind backend to 8080`, `Run migrations and seed on backend container start`, три подряд `Revert`), что само по себе сигнал: деплой дался тяжело, было несколько неудачных попыток конфигурации, которые откатывали. Один осмысленный релиз — `version 1.0` (`476e4dc`), дальше — точечные правки прод-конфигурации.

## Стек

| Слой | Технология | Версия |
|---|---|---|
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS | Next 14.2.35, React 18.3.1, TS 5.4.5, Tailwind 3.4.4 |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 | Python 3.12 (Docker-образ), FastAPI 0.115.0 |
| БД | PostgreSQL (образ `pgvector/pgvector:pg16`) | 16, расширение pgvector установлено, но **не используется нигде в коде/миграциях** — задел под будущие эмбеддинги RAG, простаивает |
| Кэш / rate limit / одноразовые токены | Redis 7 | `redis-py` async-клиент |
| Auth | JWT (`python-jose`, HS256) + `passlib[bcrypt]`, VK ID OAuth | Access-токен 60 мин, refresh-токен 30 дней (фронтенд refresh не использует, см. `03-live-vs-code.md`) |
| AI-сервис | Внешний HTTP-сервис по контракту `docs/ai-service-contract.md` | **Не существует как задеплоенный сервис.** Заглушен через `AI_SERVICE_MOCK=true` |
| Инфраструктура | Docker Compose (`db`, `redis`, `backend`, `frontend`) | Прод — RelaxDev (отдельный реверс-прокси, см. `axiom-mvp.relaxdev.ru` / `axiombackend.relaxdev.ru`) |
| Тесты | pytest + pytest-asyncio (backend, 33 теста) | Frontend — тестов нет вообще |

## Структура репозитория

```
axiom-backend/
  app/
    api/v1/          — auth, dashboard, diagnostics, trainer, assistant (5 роутеров)
    core/             — config, security (JWT/bcrypt), rate_limit (Redis), ai_client (mock/real),
                        answer_check (нормализация ответа), email (SMTP/лог), vk_oauth, redis
    db/session.py     — async engine/session, декларативная Base
    models/           — user, diagnostics, trainer, assistant (SQLAlchemy ORM)
    schemas/          — Pydantic-схемы запросов/ответов, 1:1 с models
    seed_tasks.py      — идемпотентный сид банка заданий тренажёра (45 шт.)
  alembic/versions/   — 5 линейных миграций, без ветвления
  tests/               — 33 теста (auth, dashboard, diagnostics, trainer, assistant, rate_limit)
  Dockerfile, entrypoint.sh (миграции + сид + запуск uvicorn на старте контейнера)

axiom-frontend/
  app/                — App Router: /, /login, /register, /auth/vk/callback, /forgot-password,
                        /reset-password, /dashboard, /diagnostics, /trainer, /assistant
  components/         — Shell (навигация), ui (Button/TextField)
  lib/                — api.ts (fetch-обёртка + токен в localStorage), auth.tsx (AuthContext)
  Dockerfile           — multi-stage, NEXT_PUBLIC_API_URL зашивается в билд-тайме (build arg)

docs/
  ai-service-contract.md — единственный документ в docs/ до этого аудита

docker-compose.yml     — db (pgvector/pg16) + redis + backend (uvicorn --reload) + frontend
.env.example            — шаблон переменных окружения
README.md               — подробный статус-отчёт разработчика (см. 04-documentation-gap-analysis.md)

(в корне, не в docs/):
Паспорт проекта AXIOM (трек «Стартап» 2025).xlsx
Задание 2. Подготовка Custdev.xlsx
Питч-дек AXIOM.pptx
```

## Карта функциональных доменов

| Домен | Backend | Frontend | Хранение | Статус ИИ-части |
|---|---|---|---|---|
| Auth (email, VK ID, сброс пароля, согласие 152-ФЗ, rate limit) | `api/v1/auth.py` | `/login`, `/register`, `/auth/vk/callback`, `/forgot-password`, `/reset-password` | `users` | Не применимо — нет ИИ |
| Личный кабинет / дашборд | `api/v1/dashboard.py` | `/dashboard` | Читает `diagnostic_results` | Зависит от диагностики → сейчас фиктивные данные |
| Диагностика (CAT/IRT) | `api/v1/diagnostics.py` | `/diagnostics` | `diagnostic_sessions/answers/results` | **Полностью замокано** — фиксированные 3 вопроса по математике, фиксированный результат |
| Тренажёр | `api/v1/trainer.py` | `/trainer` | `trainer_tasks`, `task_attempts` | Детерминированное правило, не ML — задумано так и это нормально для MVP |
| ИИ-ассистент (чат) | `api/v1/assistant.py` | `/assistant` | `chat_sessions/messages` | **Полностью замокано** — одна и та же строка-заглушка, без RAG |

## Что отсутствует как класс функциональности (важно для карты, детали — в других документах)

Нет: лендинга/маркетинговой страницы, страницы цен, оплаты/подписки/биллинга (ни одной таблицы/поля), админ-панели для контента, аналитики/телеметрии (ни одного события), онбординга (визуального обучения продукту до регистрации), мобильного приложения, Telegram-бота, RAG/векторного поиска (несмотря на образ БД с pgvector), Deep Knowledge Tracing, RL-планировщика, авто-проверки развёрнутых ответов.

## Как приложение запускается и тестируется (Фаза 0, пункт 5)

```bash
cp .env.example .env
docker compose up --build
# затем
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed_tasks
```
Backend: `:8000/docs` (локально; на новых образах — `:8080`, см. `47ef249`). Frontend: `:3000`.

Backend-тесты: `pytest -v` в `axiom-backend/` (нужны отдельные `axiom_test` Postgres-БД и Redis DB `/1`, `AI_SERVICE_MOCK=true` выставляется автоматически в `conftest.py`).

Frontend: `npm run build` / `next lint` / `tsc --noEmit`. Тестов (Jest/Playwright/Cypress) нет.

Фактический результат прогона в среде аудита — см. `02-runtime-audit.md`.
