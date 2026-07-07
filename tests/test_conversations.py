def _send_message(client, conversation_id="conv-1", message="Hi there"):
    return client.post(
        "/api/chat",
        json={
            "conversation_id": conversation_id,
            "message": message,
            "use_rag": False,
            "use_tools": False,
            "use_agent": False,
        },
    )


def test_list_conversations_requires_auth(client):
    res = client.get("/api/conversations")
    assert res.status_code == 401


def test_conversation_created_via_chat_is_listed(auth_client):
    _send_message(auth_client, conversation_id="conv-1")

    res = auth_client.get("/api/conversations")
    assert res.status_code == 200
    convs = res.json()
    assert len(convs) == 1
    assert convs[0]["id"] == "conv-1"
    assert convs[0]["message_count"] == 2  # user + assistant


def test_get_messages_for_conversation(auth_client):
    _send_message(auth_client, conversation_id="conv-2", message="What is 2+2?")

    res = auth_client.get("/api/conversations/conv-2/messages")
    assert res.status_code == 200
    messages = res.json()
    assert [m["role"] for m in messages] == ["user", "assistant"]


def test_get_messages_for_missing_conversation_404s(auth_client):
    res = auth_client.get("/api/conversations/does-not-exist/messages")
    assert res.status_code == 404


def test_rename_conversation(auth_client):
    _send_message(auth_client, conversation_id="conv-3")

    res = auth_client.patch("/api/conversations/conv-3/title?title=My%20Renamed%20Chat")
    assert res.status_code == 200
    assert res.json()["title"] == "My Renamed Chat"


def test_delete_conversation(auth_client):
    _send_message(auth_client, conversation_id="conv-4")

    res = auth_client.delete("/api/conversations/conv-4")
    assert res.status_code == 204

    res = auth_client.get("/api/conversations/conv-4/messages")
    assert res.status_code == 404
