import pytest


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


async def test_skill_map_requires_auth(client):
    resp = await client.get("/api/v1/trainer/skill-map", params={"subject": "math"})
    assert resp.status_code == 401


async def test_skill_map_invalid_subject(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/skill-map", params={"subject": "chemistry"}, headers=headers
    )
    assert resp.status_code == 422


async def test_skill_map_empty_for_subject_without_tasks(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/skill-map", params={"subject": "russian"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_skill_map_shows_unattempted_topic(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get(
        "/api/v1/trainer/skill-map", params={"subject": "math"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == [{"topic": "Тест", "ability_score": None, "attempts_count": 0}]


async def test_skill_map_updates_via_ewma_after_attempts(client, auth_headers):
    """new = old*0.8 + result*0.2, см. _update_knowledge_state в trainer.py."""
    headers, _ = auth_headers
    task = (
        await client.get(
            "/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers
        )
    ).json()

    await client.post(
        "/api/v1/trainer/submit", headers=headers, json={"task_id": task["id"], "answer": "999"}
    )
    after_wrong = (
        await client.get("/api/v1/trainer/skill-map", params={"subject": "math"}, headers=headers)
    ).json()[0]
    assert after_wrong["ability_score"] == 0.0
    assert after_wrong["attempts_count"] == 1

    correct_answer = "4" if "2 + 2" in task["question"] else "6"
    await client.post(
        "/api/v1/trainer/submit", headers=headers, json={"task_id": task["id"], "answer": correct_answer}
    )
    after_right = (
        await client.get("/api/v1/trainer/skill-map", params={"subject": "math"}, headers=headers)
    ).json()[0]
    assert after_right["ability_score"] == pytest.approx(0.2)
    assert after_right["attempts_count"] == 2


async def test_next_task_prioritizes_weaker_topic_by_knowledge_state(client, auth_headers):
    """_pick_topic теперь берёт ability_score из knowledge_state (EWMA), а не
    пересчитывает accuracy отдельным join-запросом — этот тест проверяет
    именно поведение, а не то, что оно берётся из правильной таблицы.

    trainer_tasks НЕ очищается между тестами (это контент, сидится один раз
    на сессию — см. tests/conftest.py), поэтому добавленную сюда задачу нужно
    удалить в конце теста самостоятельно, иначе она попадёт в другие тесты."""
    from app.db.session import AsyncSessionLocal
    from app.models.trainer import TrainerTask

    async with AsyncSessionLocal() as db:
        weak_task = TrainerTask(
            subject="math", topic="Слабая тема", difficulty=1,
            question="1 + 1 = ?", options=None, correct_answer="2",
            explanation="Простое сложение.",
        )
        db.add(weak_task)
        await db.commit()
        await db.refresh(weak_task)
        weak_task_id = weak_task.id

    try:
        headers, _ = auth_headers

        # Тема "Тест" (из общего сида) — верный ответ, ability станет 1.0
        strong_task = (
            await client.get("/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers)
        ).json()
        # next-task мог отдать либо "Тест", либо "Слабая тема" (обе непройдены) —
        # добиваем обе темы по одной попытке, чтобы дальше сравнение было честным.
        while strong_task["topic"] != "Тест":
            await client.post(
                "/api/v1/trainer/submit", headers=headers,
                json={"task_id": strong_task["id"], "answer": "wrong"},
            )
            strong_task = (
                await client.get("/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers)
            ).json()

        correct_answer = "4" if "2 + 2" in strong_task["question"] else "6"
        await client.post(
            "/api/v1/trainer/submit", headers=headers,
            json={"task_id": strong_task["id"], "answer": correct_answer},
        )

        # Теперь добиваем "Слабую тему" неверным ответом — её ability останется 0.0
        remaining = (
            await client.get("/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers)
        ).json()
        if remaining["topic"] == "Слабая тема":
            await client.post(
                "/api/v1/trainer/submit", headers=headers,
                json={"task_id": remaining["id"], "answer": "wrong"},
            )

        skill_map = (
            await client.get("/api/v1/trainer/skill-map", params={"subject": "math"}, headers=headers)
        ).json()
        by_topic = {t["topic"]: t["ability_score"] for t in skill_map}
        assert by_topic["Слабая тема"] < by_topic["Тест"]

        next_pick = (
            await client.get("/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers)
        ).json()
        assert next_pick["topic"] == "Слабая тема"
    finally:
        # Сначала попытки (FK на trainer_tasks без ON DELETE CASCADE — см.
        # docs/security/security-audit.md, находка H5), потом само задание.
        from sqlalchemy import delete as sa_delete

        from app.models.trainer import TaskAttempt

        async with AsyncSessionLocal() as db:
            await db.execute(sa_delete(TaskAttempt).where(TaskAttempt.task_id == weak_task_id))
            await db.execute(sa_delete(TrainerTask).where(TrainerTask.id == weak_task_id))
            await db.commit()


async def test_skill_map_isolated_per_user(client, auth_headers):
    headers, _ = auth_headers
    task = (
        await client.get(
            "/api/v1/trainer/next-task", params={"subject": "math"}, headers=headers
        )
    ).json()
    await client.post(
        "/api/v1/trainer/submit", headers=headers, json={"task_id": task["id"], "answer": "999"}
    )

    await client.post(
        "/api/v1/auth/register",
        json={"email": "skillmap_peer@example.com", "password": "testpassword123", "grade": 9,
              "parental_consent": True},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "skillmap_peer@example.com", "password": "testpassword123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    other_map = (
        await client.get("/api/v1/trainer/skill-map", params={"subject": "math"}, headers=other_headers)
    ).json()
    assert other_map == [{"topic": "Тест", "ability_score": None, "attempts_count": 0}]
