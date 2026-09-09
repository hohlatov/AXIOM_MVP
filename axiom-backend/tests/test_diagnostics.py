async def _drain_mock_session(client, headers, subject="math"):
    start = await client.post(
        "/api/v1/diagnostics/start", params={"subject": subject}, headers=headers
    )
    assert start.status_code == 201
    body = start.json()
    session_id = body["session_id"]
    item = body["item"]
    while not item["is_final"]:
        resp = await client.post(
            "/api/v1/diagnostics/answer",
            headers=headers,
            json={"session_id": session_id, "item_id": item["item_id"], "answer": "8"},
        )
        assert resp.status_code == 200
        item = resp.json()["item"]
    return session_id


async def test_full_diagnostic_flow(client, auth_headers):
    headers, _ = auth_headers
    session_id = await _drain_mock_session(client, headers)

    result = await client.post(f"/api/v1/diagnostics/{session_id}/finalize", headers=headers)
    assert result.status_code == 200
    topics = result.json()["topics"]
    assert len(topics) > 0
    assert any(t["weak"] for t in topics)


async def test_finalize_idempotent(client, auth_headers):
    headers, _ = auth_headers
    session_id = await _drain_mock_session(client, headers)
    first = await client.post(f"/api/v1/diagnostics/{session_id}/finalize", headers=headers)
    second = await client.post(f"/api/v1/diagnostics/{session_id}/finalize", headers=headers)
    assert first.json() == second.json()


async def test_answer_on_completed_session_conflicts(client, auth_headers):
    headers, _ = auth_headers
    session_id = await _drain_mock_session(client, headers)
    await client.post(f"/api/v1/diagnostics/{session_id}/finalize", headers=headers)

    resp = await client.post(
        "/api/v1/diagnostics/answer",
        headers=headers,
        json={"session_id": session_id, "item_id": "mock-1", "answer": "1"},
    )
    assert resp.status_code == 409


async def test_finalize_nonexistent_session_404(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/diagnostics/00000000-0000-0000-0000-000000000000/finalize", headers=headers
    )
    assert resp.status_code == 404


async def test_other_user_cannot_access_session(client, auth_headers):
    headers, _ = auth_headers
    session_id = await _drain_mock_session(client, headers)

    await client.post(
        "/api/v1/auth/register",
        json={"email": "intruder@example.com", "password": "testpassword123", "grade": 9, "parental_consent": True},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "intruder@example.com", "password": "testpassword123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(f"/api/v1/diagnostics/{session_id}/result", headers=other_headers)
    assert resp.status_code == 404
