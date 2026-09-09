async def test_chat_requires_auth(client):
    resp = await client.post(
        "/api/v1/assistant/chat", json={"subject": "math", "message": "привет"}
    )
    assert resp.status_code == 401


async def test_chat_requires_subject_for_new_session(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/assistant/chat", headers=headers, json={"message": "привет"}
    )
    assert resp.status_code == 422


async def test_chat_creates_and_continues_session(client, auth_headers):
    headers, _ = auth_headers
    first = await client.post(
        "/api/v1/assistant/chat",
        headers=headers,
        json={"subject": "math", "message": "Как решать уравнения?"},
    )
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    second = await client.post(
        "/api/v1/assistant/chat",
        headers=headers,
        json={"session_id": session_id, "message": "А если корней нет?"},
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id

    history = await client.get(
        f"/api/v1/assistant/sessions/{session_id}/history", headers=headers
    )
    assert history.status_code == 200
    roles = [m["role"] for m in history.json()]
    assert roles == ["user", "assistant", "user", "assistant"]


async def test_chat_nonexistent_session_404(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/assistant/chat",
        headers=headers,
        json={"session_id": "00000000-0000-0000-0000-000000000000", "message": "тест"},
    )
    assert resp.status_code == 404


async def test_other_user_cannot_access_session(client, auth_headers):
    headers, _ = auth_headers
    first = await client.post(
        "/api/v1/assistant/chat", headers=headers, json={"subject": "math", "message": "тест"}
    )
    session_id = first.json()["session_id"]

    await client.post(
        "/api/v1/auth/register",
        json={"email": "intruder2@example.com", "password": "testpassword123", "grade": 9, "parental_consent": True},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "intruder2@example.com", "password": "testpassword123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        f"/api/v1/assistant/sessions/{session_id}/history", headers=other_headers
    )
    assert resp.status_code == 404
