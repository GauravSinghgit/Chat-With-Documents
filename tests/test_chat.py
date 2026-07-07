def test_chat_standard_path_uses_fake_llm(client):
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": "c1",
            "message": "Hello",
            "use_rag": False,
            "use_tools": False,
            "use_agent": False,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["message"] == "fake llm answer"
    assert body["conversation_id"] == "c1"


def test_chat_agent_path_uses_fake_agent(client):
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": "c2",
            "message": "What is 2 + 2?",
            "use_agent": True,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["message"] == "fake agent answer"


def test_chat_stream_emits_tokens_and_done_event(client):
    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "conversation_id": "c3",
            "message": "Stream this",
            "use_rag": False,
            "use_tools": False,
        },
    ) as res:
        assert res.status_code == 200
        chunks = [line for line in res.iter_lines() if line]

    assert any('"type": "token"' in c for c in chunks)
    assert any('"type": "done"' in c for c in chunks)


def test_anonymous_chat_does_not_require_auth(client):
    res = client.post(
        "/api/chat",
        json={"conversation_id": "c4", "message": "no login needed"},
    )
    assert res.status_code == 200
