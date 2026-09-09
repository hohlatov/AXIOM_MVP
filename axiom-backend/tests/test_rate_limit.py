"""
Тесты на срабатывание rate limiting. Используют пороги из auth.py напрямую
(не задают свои — если пороги в коде поменяются, тест должен продолжать
проверять «превысили лимит → 429», а не конкретное число N)."""
from app.api.v1 import auth as auth_module


async def test_login_email_rate_limit_returns_429(client):
    email = "bruteforce_target@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correctpassword123", "grade": 9, "parental_consent": True},
    )

    limit = 5  # см. rate_limit_by_key("login-email", ..., max_requests=5, ...) в auth.py
    last_status = None
    for _ in range(limit + 2):
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
        )
        last_status = resp.status_code

    assert last_status == 429
    assert "Retry-After" in resp.headers


async def test_register_ip_rate_limit_returns_429(client):
    limit = 5  # rate_limit_by_ip("register", max_requests=5, ...)
    last_status = None
    for i in range(limit + 2):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": f"spam{i}@example.com", "password": "testpassword123", "grade": 9, "parental_consent": True},
        )
        last_status = resp.status_code

    assert last_status == 429


async def test_password_reset_request_email_rate_limit(client):
    email = "reset_target@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "grade": 9, "parental_consent": True},
    )

    limit = 3  # rate_limit_by_key("pwreset-request-email", ..., max_requests=3, ...)
    last_status = None
    for _ in range(limit + 2):
        resp = await client.post("/api/v1/auth/password-reset/request", json={"email": email})
        last_status = resp.status_code

    assert last_status == 429


async def test_rate_limit_does_not_leak_across_different_emails(client):
    """Лимит по email не должен блокировать других пользователей."""
    for i in range(3):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "victim@example.com", "password": "wrong"},
        )

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "unrelated@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401  # не 429 — это другой email, свой лимит
