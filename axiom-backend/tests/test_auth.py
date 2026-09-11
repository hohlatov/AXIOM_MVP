from app.core.redis import get_redis


async def _register(client, email, password="testpassword123", grade=9, parental_consent=True):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "grade": grade, "parental_consent": parental_consent},
    )


async def test_register_creates_user(client):
    resp = await _register(client, "alice@example.com")
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["grade"] == 9


async def test_register_duplicate_email_conflicts(client):
    await _register(client, "bob@example.com")
    resp = await _register(client, "bob@example.com")
    assert resp.status_code == 409


async def test_login_success(client):
    await _register(client, "carol@example.com")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "carol@example.com", "password": "testpassword123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body


async def test_login_wrong_password(client):
    await _register(client, "dave@example.com")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "dave@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client, auth_headers):
    headers, email = auth_headers
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == email


async def test_password_reset_full_flow(client):
    email = "eve@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword456"
    await _register(client, email, password=old_password)

    resp = await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert resp.status_code == 202

    redis = get_redis()
    keys = await redis.keys("pwdreset:*")
    assert len(keys) == 1
    token = keys[0].split(":", 1)[1]

    bad = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "garbage", "new_password": new_password},
    )
    assert bad.status_code == 400

    ok = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": new_password},
    )
    assert ok.status_code == 200

    old_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": old_password}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": new_password}
    )
    assert new_login.status_code == 200

    reuse = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "anotherpassword"},
    )
    assert reuse.status_code == 400


async def test_password_reset_unknown_email_still_202(client):
    resp = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"}
    )
    assert resp.status_code == 202


async def test_register_without_parental_consent_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "noconsent@example.com", "password": "testpassword123", "grade": 9,
              "parental_consent": False},
    )
    assert resp.status_code == 422


async def test_register_missing_parental_consent_field_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "noconsent2@example.com", "password": "testpassword123", "grade": 9},
    )
    assert resp.status_code == 422


async def test_register_records_consent_timestamp(client):
    resp = await _register(client, "consenting@example.com")
    assert resp.status_code == 201
    body = resp.json()
    assert body["parental_consent_given"] is True


async def test_vk_login_issues_and_stores_state(client):
    resp = await client.get("/api/v1/auth/vk/login")
    assert resp.status_code == 200
    body = resp.json()
    state = body["state"]
    assert state in body["authorize_url"]

    redis = get_redis()
    assert await redis.get(f"vkstate:{state}") is not None


async def test_vk_callback_rejects_unknown_state(client):
    resp = await client.get(
        "/api/v1/auth/vk/callback",
        params={"code": "whatever", "state": "never-issued", "parental_consent": "true"},
    )
    assert resp.status_code == 400


async def test_vk_callback_state_is_one_time_use(client, monkeypatch):
    async def _fake_exchange_code(code):
        raise ValueError("stub — реального обращения к VK в тестах не делаем")

    monkeypatch.setattr("app.api.v1.auth.exchange_code", _fake_exchange_code)

    login_resp = await client.get("/api/v1/auth/vk/login")
    state = login_resp.json()["state"]

    # exchange_code застаблен и падает сразу — важно здесь не то, что вернёт
    # эндпоинт, а что state после первого использования удаляется из Redis.
    await client.get(
        "/api/v1/auth/vk/callback",
        params={"code": "whatever", "state": state, "parental_consent": "true"},
    )

    redis = get_redis()
    assert await redis.get(f"vkstate:{state}") is None

    reuse = await client.get(
        "/api/v1/auth/vk/callback",
        params={"code": "whatever", "state": state, "parental_consent": "true"},
    )
    assert reuse.status_code == 400


async def test_refresh_issues_new_working_access_token(client):
    await _register(client, "frank@example.com")
    login = await client.post(
        "/api/v1/auth/login", json={"email": "frank@example.com", "password": "testpassword123"}
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_access_token = resp.json()["access_token"]
    assert resp.json()["refresh_token"] == refresh_token  # не ротируется — см. комментарий в auth.py

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "frank@example.com"


async def test_refresh_rejects_access_token(client):
    await _register(client, "grace@example.com")
    login = await client.post(
        "/api/v1/auth/login", json={"email": "grace@example.com", "password": "testpassword123"}
    )
    access_token = login.json()["access_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


async def test_refresh_rejects_garbage_token(client):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert resp.status_code == 401


async def test_vk_callback_requires_state_param(client):
    resp = await client.get(
        "/api/v1/auth/vk/callback",
        params={"code": "whatever", "parental_consent": "true"},
    )
    assert resp.status_code == 422
