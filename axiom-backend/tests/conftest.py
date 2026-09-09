"""
Фикстуры для тестов. Использует отдельную БД axiom_test (не трогает dev/prod
данные) и отдельный индекс Redis (REDIS_URL=.../1 вместо .../0). Переменные
окружения выставляются до импорта app.* — pydantic-settings иначе подхватит
значения из .env.

Движок приложения пересоздаётся здесь с poolclass=NullPool: штатный пул
AsyncAdaptedQueuePool в связке с asyncpg периодически ловит
'another operation is in progress', когда короткоживущие сессии на запрос
чередуются с соединениями, которые открывают сами фикстуры (сидинг,
TRUNCATE между тестами). NullPool — открывает новое соединение на каждую
операцию и закрывает сразу — устраняет весь этот класс гонок; для тестов
цена по производительности не важна.

Между тестами таблицы очищаются (кроме trainer_tasks — это контент, не
пользовательские данные, сидится один раз на сессию).
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://axiom:axiom@localhost:5432/axiom_test")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("AI_SERVICE_MOCK", "true")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.db.session as db_session
from app.core.config import settings
from app.core.redis import get_redis
from app.main import app
from app.models.trainer import TrainerTask


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю сессию тестов, а не новый на каждую функцию
    (поведение pytest-asyncio по умолчанию) — иначе соединения, открытые в
    одном loop'е, оказываются непригодны в следующем. Предупреждение об
    устаревании этой фикстуры безвредно для используемой версии плагина."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_database():
    await db_session.engine.dispose()
    test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
    db_session.engine = test_engine
    db_session.AsyncSessionLocal = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(db_session.Base.metadata.drop_all)
        await conn.run_sync(db_session.Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _seed_trainer_tasks(_setup_database):
    async with db_session.AsyncSessionLocal() as db:
        db.add_all([
            TrainerTask(subject="math", topic="Тест", difficulty=1,
                        question="2 + 2 = ?", options=None, correct_answer="4",
                        explanation="Простое сложение."),
            TrainerTask(subject="math", topic="Тест", difficulty=1,
                        question="3 + 3 = ?", options=None, correct_answer="6",
                        explanation="Простое сложение."),
        ])
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _clean_between_tests():
    yield
    async with db_session.engine.begin() as conn:
        tables = [t.name for t in db_session.Base.metadata.sorted_tables if t.name != "trainer_tasks"]
        if tables:
            await conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    redis = get_redis()
    await redis.flushdb()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """Регистрирует свежего пользователя и возвращает (headers, email)."""
    email = f"user_{os.urandom(4).hex()}@example.com"
    password = "testpassword123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "grade": 9, "parental_consent": True},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email
