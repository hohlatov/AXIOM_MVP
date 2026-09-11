# 03 — Дизайн базы данных: as-is и целевая схема (Фаза 15)

> Аудит проведён: 2026-09-11. Источник — построчное чтение всех файлов `axiom-backend/app/models/*.py` (4 файла, 8 моделей) и всех 5 файлов миграций `axiom-backend/alembic/versions/*.py`. Миграции и модели сверены между собой: **расхождений не найдено** — то, что описано в ORM-моделях, 1:1 соответствует тому, что реально создают миграции. Линейная история миграций без ветвления (`dff6639b499e → c9fa9050e3fe → 7efa6085b98e → 53d8369f1115 → bc34a22e96af`), все — автосгенерированные Alembic-заготовки без ручных правок под конкретные индексы/constraints.

## 1. Схема as-is

СУБД: PostgreSQL 16 (образ `pgvector/pgvector:pg16` — расширение `pgvector` доступно в образе, но **не создано ни одной миграцией** — `CREATE EXTENSION` нигде не вызывается, векторных колонок нет ни в одной таблице). Все таблицы — 3NF по атомарности колонок, без явных нарушений нормальных форм, но с существенным дизайн-смэллом (раздел 3).

### ER-схема (текстово)

```
users (1) ──┬──< diagnostic_sessions (1) ──┬──< diagnostic_answers
            │                               └──< diagnostic_results
            ├──< task_attempts >── trainer_tasks
            └──< chat_sessions (1) ──< chat_messages
```

Ни одного ON DELETE CASCADE / SET NULL ни на одном FK — все внешние ключи созданы с поведением по умолчанию (`NO ACTION`).

### 1.1 `users`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK, default `uuid4()` на стороне приложения (не `gen_random_uuid()` в БД) |
| email | VARCHAR(255) | UNIQUE, NULL, индекс `ix_users_email` |
| vk_id | VARCHAR(64) | UNIQUE, NULL, индекс `ix_users_vk_id` |
| password_hash | VARCHAR(255) | NULL (пусто для VK-only аккаунтов) |
| grade | INTEGER | NULL, без CHECK (может быть любым числом, в т.ч. отрицательным — валидация только на уровне Pydantic при регистрации, не на уровне БД) |
| parental_consent_given | BOOLEAN | NOT NULL, default `false` (добавлено миграцией `bc34a22e96af`, 2026-09-07 — отдельно от создания таблицы) |
| parental_consent_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

**Находки:**
- Нет `updated_at` — невозможно отследить, когда менялся пароль/класс/email без отдельного аудит-лога.
- Нет CHECK-ограничения `email IS NOT NULL OR vk_id IS NOT NULL` — на уровне БД можно создать «пустого» пользователя без единого способа входа. Сейчас защищено только тем, что оба места создания `User(...)` в `auth.py` всегда передают хотя бы одно поле, но это дисциплина кода, не гарантия схемы.
- **Гонка при регистрации**: `register()` в `auth.py` сначала делает `SELECT ... WHERE email = ...`, и только потом `INSERT`. Между этими двумя операциями два параллельных запроса с одним email пройдут проверку одновременно; второй `INSERT` упадёт на UNIQUE-констрейнте `ix_users_email`, но код **не перехватывает `IntegrityError`** — вместо ожидаемого `409 Conflict` клиент получит необработанный `500`. Уникальный индекс защищает данные, но не UX/контракт API. Проверено: `axiom-backend/app/api/v1/auth.py:47-62`.
- `password_hash` без `NOT NULL` — корректно для VK-only пользователей, но нет ограничения «пароль или vk_id обязателен», симметрично предыдущему пункту.

### 1.2 `diagnostic_sessions`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → `users.id`, индекс `ix_diagnostic_sessions_user_id` |
| subject | VARCHAR(32) | NOT NULL, **свободная строка**, на уровне API ограничена regex `^(math\|russian)$`, но не на уровне БД |
| status | VARCHAR(16) | NOT NULL, default `"in_progress"` — свободная строка, не PostgreSQL ENUM, допустимые значения (`in_progress`/`completed`) не закреплены CHECK-ограничением |
| started_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |
| completed_at | TIMESTAMPTZ | NULL |

**Находки:** нет составного индекса `(user_id, subject, status)`, хотя именно по этой тройке идёт основной запрос дашборда (`_latest_completed_session` в `dashboard.py:25-32`, с `ORDER BY completed_at DESC LIMIT 1`). При 100 пользователях это не заметно (последовательное сканирование по индексу `user_id` за миллисекунды), но это первый кандидат на индекс при росте объёма диагностических сессий.

### 1.3 `diagnostic_answers`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| session_id | UUID | FK → `diagnostic_sessions.id`, индекс `ix_diagnostic_answers_session_id` |
| item_id | VARCHAR(64) | NOT NULL — идентификатор вопроса, присваивается ИИ-сервисом (или мок-словарём), не связан FK ни с чем, потому что банка диагностических вопросов как таблицы в БД **не существует** — вопросы существуют только внутри ИИ-сервиса/мока |
| answer | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

**Находка:** нет UNIQUE(`session_id`, `item_id`) — при повторной отправке ответа на один и тот же `item_id` (например, двойной клик или retry по таймауту) в таблице накопится несколько строк с одинаковым вопросом, что исказит `previous_answers`, передаваемые ИИ-сервису при следующем шаге (`_get_answers` в `diagnostics.py:114-116` возвращает их все без дедупликации).

### 1.4 `diagnostic_results`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| session_id | UUID | FK → `diagnostic_sessions.id`, индекс `ix_diagnostic_results_session_id` |
| topic | VARCHAR(128) | NOT NULL — **свободная строка**, не FK на справочник тем |
| ability_score | FLOAT | NOT NULL, ожидаемый диапазон 0.0–1.0, **не ограничен CHECK-констрейнтом** — БД примет `ability_score = 500` |
| weak | BOOLEAN | NOT NULL, default `false` |

### 1.5 `trainer_tasks`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| subject | VARCHAR(32) | NOT NULL, свободная строка ("math"/"russian" по конвенции кода) |
| topic | VARCHAR(128) | NOT NULL, свободная строка ("Уравнения", "Проценты" и т.д. — ровно та же проблема, что и в `diagnostic_results.topic`, но это **два независимых текстовых поля без какой-либо связи между собой**: тема "Уравнения" из диагностики и тема "Уравнения" из тренажёра совпадают только потому, что кто-то вручную использовал одинаковую строку) |
| difficulty | INTEGER | NOT NULL, default 1, диапазон 1–5 по конвенции комментария в модели, **не проверяется CHECK-ограничением** |
| question | TEXT | NOT NULL |
| options | VARCHAR[] (ARRAY) | NULL — `NULL` = задание со свободным ответом, непустой массив = задание с вариантами. Семантика через `NULL` вместо явного поля `task_type`, что затрудняет будущие типы заданий (например, "несколько правильных ответов") |
| correct_answer | VARCHAR(255) | NOT NULL |
| explanation | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

**Находка:** нет индекса на `(subject, topic)`, хотя это основной паттерн выборки (`trainer.py:29,82`: `WHERE subject = ? AND topic = ?`, плюс `SELECT DISTINCT topic WHERE subject = ?`). При 45 строках — не важно; при росте банка заданий до тысяч (Stage 2, где подготовка к ОГЭ по всем темам обоих предметов подразумевает на порядок больше контента) — обязательный индекс.

### 1.6 `task_attempts`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → `users.id`, индекс `ix_task_attempts_user_id` |
| task_id | UUID | FK → `trainer_tasks.id`, индекс `ix_task_attempts_task_id` |
| submitted_answer | VARCHAR(255) | NOT NULL |
| is_correct | BOOLEAN | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

**Находка:** запрос подбора темы в `trainer.py:36-46` делает `JOIN task_attempts ON task_id` + `GROUP BY topic`, фильтруя по `user_id` и `subject` — под эту связку не хватает составного индекса `(user_id, task_id)` или, лучше, покрывающего индекса `(task_id, user_id, is_correct)`; сейчас Postgres использует раздельные индексы на `user_id`/`task_id` и делает bitmap-merge, что при 45 заданиях/100 пользователях абсолютно незаметно, но это первая точка деградации при росте контент-банка и базы пользователей.

### 1.7 `chat_sessions`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → `users.id`, индекс `ix_chat_sessions_user_id` |
| subject | VARCHAR(32) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

### 1.8 `chat_messages`

| Колонка | Тип | Constraints |
|---|---|---|
| id | UUID | PK |
| session_id | UUID | FK → `chat_sessions.id`, индекс `ix_chat_messages_session_id` |
| role | VARCHAR(16) | NOT NULL, `"user"` \| `"assistant"` по конвенции, без CHECK |
| content | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, `server_default now()` |

**Находка:** `assistant.py:71-86` (`GET /sessions/{id}/history`) отдаёт **весь** список сообщений `ORDER BY created_at`, без `LIMIT`/пагинации/курсора. Для MVP с короткими сессиями это не проблема; для длинной пользовательской сессии с ИИ-репетитором (что и есть ценностное предложение продукта) список неограниченно растёт при каждом открытии истории.

## 2. Итоговая инвентаризация: 8 таблиц

`users`, `diagnostic_sessions`, `diagnostic_answers`, `diagnostic_results`, `trainer_tasks`, `task_attempts`, `chat_sessions`, `chat_messages`. Все с суррогатным UUID PK, все внешние ключи индексированы (Alembic автогенерация это делает по умолчанию для FK-колонок) — это минимально достаточная гигиена индексов, но не более того: ни одного составного/покрывающего индекса под реальные паттерны запросов из роутеров нет нигде.

## 3. Оценка нормализации и качества модели данных

Формально каждая таблица в 3NF: нет повторяющихся групп, все атрибуты атомарны, нет транзитивных зависимостей внутри одной таблицы. Но есть системная проблема **на уровне доменного моделирования**, не строгой нормализации:

**"Стрингово-типизированный" домен вместо справочников.** `subject` (`"math"` / `"russian"`) и `topic` (`"Уравнения"`, `"Проценты"` и т.д.) существуют как свободный `VARCHAR` в трёх независимых местах: `trainer_tasks.topic`, `diagnostic_results.topic`, и неявно — в ответах мок-ИИ-сервиса (`ai_client.py:53-56`, темы "Уравнения"/"Проценты" захардкожены прямо в Python-словаре). Ничто на уровне БД не гарантирует, что "Уравнения" в тренажёре и "Уравнения" из диагностики — один и тот же концепт: опечатка, регистр, лишний пробел — и связь молча рвётся, а рекомендации дашборда (`get_recommendations` в `dashboard.py:52-65`) для этой темы перестанут находить задания в тренажёре. Это прямо описано в самой директиве аудита (Фаза 15: subjects/topics/skills как отдельные сущности vs строки) — здесь однозначно **вариант "захардкоженные строки"**, не сущности.

**Нет иерархии Topic → Skill → Subskill.** Директива (Фаза 11) предполагает граф `Тема → Навык → Поднавык → Пререквизит`. В коде этого нет вообще — есть только плоский `topic: str`. Для ОГЭ, где, например, тема "Уравнения" разваливается на линейные/квадратные/дробно-рациональные с разными пререквизитами, это существенное упрощение, оправданное для MVP на 45 заданиях, но не масштабируемое без изменения схемы.

## 4. Отсутствующие сущности (из требований директивы)

Прямая сверка с Фазой 15 директивы («users, students, subjects, topics, skills, tasks, attempts, errors, knowledge_state, recommendations, AI conversations, subscriptions, payments, аналитика»):

| Сущность из директивы | Статус | Комментарий |
|---|---|---|
| users | ЕСТЬ | `users`, без ролей (нет `role`/RBAC-поля — все пользователи неявно "ученики") |
| students | ОТСУТСТВУЕТ как отдельная сущность | `users` = студент напрямую, нет разделения "учётная запись" vs "профиль ученика" — нормально для MVP, станет проблемой при вводе ролей учитель/родитель/завуч (Stage 3) |
| subjects | ОТСУТСТВУЕТ как таблица | Захардкожен `SUBJECT_LABELS = {"math": ..., "russian": ...}` в `dashboard.py:22`, regex `^(math\|russian)$` в роутерах |
| topics | ОТСУТСТВУЕТ как таблица | Свободная строка, см. раздел 3 |
| skills | ОТСУТСТВУЕТ полностью | Нет ни таблицы, ни понятия в коде |
| tasks | ЕСТЬ (частично) | `trainer_tasks` — только тренажёр. Банка вопросов для диагностики как таблицы **нет** — вопросы генерирует ИИ-сервис (или мок в Python-коде), не хранятся в БД |
| attempts | ЕСТЬ | `task_attempts` (только тренажёр), `diagnostic_answers` (сырые ответы диагностики, без явного `is_correct` — корректность решает ИИ-сервис на своей стороне, backend её не хранит) |
| errors | ОТСУТСТВУЕТ как отдельная сущность | Есть `is_correct=false` в `task_attempts` и `explanation` в `trainer_tasks`, но нет классификации типа ошибки (вычислительная/концептуальная/невнимательность и т.п.) — для Фазы 11 (`Error Pattern`) это прямой пробел |
| knowledge_state | ОТСУТСТВУЕТ как хранимая сущность | Прогресс на дашборде вычисляется "на лету" из `DiagnosticResult.ability_score` (`dashboard.py:35-49`) — нет персистентного, инкрементально обновляемого состояния знаний ученика по навыкам; каждое обращение к дашборду — full re-aggregation по последней диагностике, тренажёр вообще не влияет на `ability_score` |
| recommendations | ОТСУТСТВУЕТ как хранимая сущность | Вычисляются на лету из `weak=true` результатов диагностики (`dashboard.py:52-65`), не сохраняются, не имеют истории/статуса "выполнено/отклонено" |
| AI conversations | ЕСТЬ | `chat_sessions` + `chat_messages` — история чата с ассистентом реально сохраняется (это лучше, чем можно было ожидать от MVP с моком вместо ИИ) |
| subscriptions | ОТСУТСТВУЕТ полностью | Ни таблицы, ни поля где-либо — ожидаемо для MVP без биллинга, но потребуется до Stage 2 (см. `02-target-architecture.md`) |
| payments | ОТСУТСТВУЕТ полностью | Аналогично |
| аналитика (events) | ОТСУТСТВУЕТ полностью | Нет таблицы `events`, нет интеграции с внешним аналитическим сервисом — см. `docs/product/analytics-spec.md` |

Дополнительно отсутствует (не в списке директивы, но важно для целостности системы): таблица `refresh_tokens`/`revoked_tokens`. `create_refresh_token()` (`app/core/security.py:30-31`) генерирует refresh-JWT на 30 дней, он возвращается клиенту в `TokenPair` при регистрации/логине/VK-логине — но **ни одного эндпоинта `/auth/refresh`, который бы принимал этот токен и обменивал его на новый access-токен, в API нет** (проверено — `grep -r refresh` по всему backend не находит роута, только генерацию и упоминание в тесте `test_auth.py:32`, которое просто проверяет наличие поля в ответе). Это не просто «фронтенд не использует» (как зафиксировано в `02-runtime-audit.md`) — это **бэкенд не реализует функциональность, чей артефакт (сам токен) уже выдаётся пользователю**. Токен висит валидным 30 дней без единого способа его использовать или отозвать.

## 5. Row-Level Security (RLS)

**RLS не используется вообще** — ни в одной таблице. Изоляция данных между пользователями обеспечивается исключительно на уровне application-кода: каждый роутер вручную проверяет `session.user_id == user.id` перед возвратом данных (например, `diagnostics.py:56`, `diagnostics.py:82`, `assistant.py:31`, `assistant.py:78`). Это стандартный и приемлемый подход для монолита с одним доверенным backend-процессом на MVP-масштабе — включать RLS ради 100 пользователей было бы избыточной сложностью (соответствует принципу CLAUDE.md «не решать проблему, которой пока нет»). Риск в том, что эта изоляция **не защищена тестами на уровне «чужая сессия»** системно — по коду видно точечные проверки в каждом роутере, но нет единого review-чеклиста/теста, что при добавлении нового эндпоинта разработчик не забудет эту проверку скопировать.

## 6. Паттерны запросов — итоговая оценка

Все запросы, прочитанные в роутерах, используют `async` SQLAlchemy 2.0 ORM корректно (`select()`, `scalar()`, `scalars()`), без N+1 в критичных путях (агрегации в `dashboard.py`/`trainer.py` явно используют `GROUP BY`/`func.count`/`func.sum` на стороне БД, а не постфактум в Python). Пул соединений — дефолтный SQLAlchemy `AsyncAdaptedQueuePool` (`db/session.py:6`, `pool_size`/`max_overflow` не заданы явно → SQLAlchemy default 5/10), без `pool_pre_ping=True` — на долгоживущем соединении с Postgres за NAT/прокси это может изредка давать "stale connection" ошибки после простоя; для 100 пользователей маловероятно, стоит держать в уме при переходе на несколько backend-реплик.

## 7. Целевая схема для Stage 2 (коммерческий запуск, 1 000–10 000 пользователей)

Явно отделяю: это **предложение**, ничего из этого раздела не реализовано.

```
subjects            (id, code, name)                                    -- заменяет строковый subject
topics               (id, subject_id FK, code, name, order)               -- заменяет строковый topic
skills                (id, topic_id FK, name, prerequisite_skill_id FK NULL) -- граф навыков (Фаза 9/11)
tasks                 (было trainer_tasks; + skill_id FK вместо topic:str)
diagnostic_items      (новая — банк вопросов диагностики как данные, а не только в голове ИИ-сервиса/мока;
                        нужна, если диагностика перестанет быть полностью generative)
task_attempts         (без изменений структуры, + FK на skill_id через task_id)
knowledge_state       (id, user_id FK, skill_id FK, mastery FLOAT, updated_at, UNIQUE(user_id, skill_id))
                       -- персистентное, инкрементально обновляемое состояние — заменяет "на лету"
                          пересчёт из diagnostic_results на каждый вызов /dashboard/summary
recommendations       (id, user_id FK, skill_id FK, reason, status, created_at, resolved_at)
                       -- сохранённые рекомендации с состоянием "показана/принята/выполнена"
chat_sessions/messages (без структурных изменений; добавить token_count/cost_usd на message
                        для контроля стоимости ИИ, см. technical-debt.md)
subscriptions          (id, user_id FK, plan, status, current_period_end, provider_id)
payments               (id, user_id FK, subscription_id FK, amount, currency, status, provider, external_id)
refresh_tokens          (id, user_id FK, token_hash, expires_at, revoked_at NULL)
                       -- необходимо, если /auth/refresh наконец появится — иначе не 
                          из чего отзывать токен при компрометации/логауте
events                 (id, user_id FK NULL, event_name, properties JSONB, created_at)
                       -- см. docs/product/analytics-spec.md — либо своя таблица, либо
                          внешний сервис (PostHog self-hosted/облачный) — сама эта таблица
                          не обязана жить в основной OLTP-базе уже на Stage 2
```

Дополнительно на Stage 2 стоит добавить недостающие CHECK-констрейнты (`ability_score BETWEEN 0 AND 1`, `difficulty BETWEEN 1 AND 5`, `role IN (...)` при появлении ролей), `ON DELETE CASCADE` на всех FK от `users` (для права на удаление аккаунта/данных по 152-ФЗ — сейчас удаление пользователя технически невозможно без ручной предварительной очистки всех дочерних таблиц, что не реализовано нигде), и составные индексы, перечисленные в разделах 1.2/1.5/1.6.

`pgvector` стоит либо начать использовать (эмбеддинги для RAG-поиска по базе ОГЭ, если Stage 2 подтвердит, что RAG оправдан — см. `docs/architecture/ai-tutor.md`), либо осознанно убрать образ БД на обычный `postgres:16`, чтобы не тащить неиспользуемую зависимость в продакшен-образ бездумно.

## Источники
- `axiom-backend/app/models/user.py`, `diagnostics.py`, `trainer.py`, `assistant.py`
- `axiom-backend/alembic/versions/dff6639b499e_*.py`, `c9fa9050e3fe_*.py`, `7efa6085b98e_*.py`, `53d8369f1115_*.py`, `bc34a22e96af_*.py`
- `axiom-backend/app/api/v1/auth.py`, `dashboard.py`, `diagnostics.py`, `trainer.py`, `assistant.py`
- `axiom-backend/app/core/security.py`, `db/session.py`, `ai_client.py`
- `axiom-backend/tests/test_auth.py`, `tests/conftest.py`
- `docs/audit/02-runtime-audit.md` (сверка находки про refresh-токен)
