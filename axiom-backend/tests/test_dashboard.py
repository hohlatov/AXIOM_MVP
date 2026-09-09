async def test_dashboard_before_diagnostic(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_diagnostic_result"] is False
    assert all(p["percent"] == 0 for p in body["progress"])
    assert "assistant" in body["quick_actions"]


async def test_dashboard_after_diagnostic_shows_real_progress(client, auth_headers):
    headers, _ = auth_headers
    start = await client.post(
        "/api/v1/diagnostics/start", params={"subject": "math"}, headers=headers
    )
    session_id = start.json()["session_id"]
    item = start.json()["item"]
    while not item["is_final"]:
        resp = await client.post(
            "/api/v1/diagnostics/answer",
            headers=headers,
            json={"session_id": session_id, "item_id": item["item_id"], "answer": "8"},
        )
        item = resp.json()["item"]
    await client.post(f"/api/v1/diagnostics/{session_id}/finalize", headers=headers)

    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    body = resp.json()
    assert body["has_diagnostic_result"] is True
    math_progress = next(p for p in body["progress"] if p["subject"] == "math")
    assert math_progress["percent"] > 0
    assert len(body["recommendations"]) > 0
