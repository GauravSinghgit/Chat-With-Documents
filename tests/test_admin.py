def test_stats_requires_auth(client):
    res = client.get("/api/admin/stats")
    assert res.status_code == 401


def test_stats_rejects_non_admin(auth_client):
    res = auth_client.get("/api/admin/stats")
    assert res.status_code == 403


def test_stats_returns_usage_totals_for_admin(admin_client):
    # Generate one usage event via a real chat request (fake LLM under the hood).
    admin_client.post(
        "/api/chat",
        json={
            "conversation_id": "admin-conv",
            "message": "hi",
            "use_rag": False,
            "use_tools": False,
        },
    )

    res = admin_client.get("/api/admin/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["totals"]["total_requests"] == 1
    assert body["totals"]["total_prompt_tokens"] == 10
    assert body["totals"]["total_completion_tokens"] == 5
    assert len(body["by_day"]) == 1
