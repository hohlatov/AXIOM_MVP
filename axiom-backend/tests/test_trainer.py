async def test_next_task_requires_auth(client):
    resp = await client.get("/api/v1/trainer/next-task", params={"subject": "math"})
    assert resp.status_code == 401


async def test_next_task_returns_seeded_task(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "math"
    assert "correct_answer" not in body  # правильный ответ не должен утекать в задание


async def test_next_task_invalid_subject(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/next-task", params={"subject": "chemistry"}, headers=headers
    )
    assert resp.status_code == 422


async def test_next_task_no_tasks_for_subject(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/next-task", params={"subject": "russian"}, headers=headers
    )
    assert resp.status_code == 404


async def test_submit_correct_and_wrong_answer(client, auth_headers):
    headers, _ = auth_headers
    task = (
        await client.get(
            "/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers
        )
    ).json()

    wrong = await client.post(
        "/api/v1/trainer/submit",
        headers=headers,
        json={"task_id": task["id"], "answer": "999"},
    )
    assert wrong.status_code == 200
    assert wrong.json()["is_correct"] is False
    assert wrong.json()["explanation"]

    correct_answer = "4" if "2 + 2" in task["question"] else "6"
    right = await client.post(
        "/api/v1/trainer/submit",
        headers=headers,
        json={"task_id": task["id"], "answer": correct_answer},
    )
    assert right.json()["is_correct"] is True


async def test_submit_nonexistent_task(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/trainer/submit",
        headers=headers,
        json={"task_id": "00000000-0000-0000-0000-000000000000", "answer": "1"},
    )
    assert resp.status_code == 404
