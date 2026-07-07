def test_register_creates_user(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "StrongPass123!", "full_name": "Alice"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "alice@example.com"
    assert body["is_admin"] is False


def test_register_duplicate_email_rejected(client):
    payload = {"email": "bob@example.com", "password": "StrongPass123!"}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400


def test_login_sets_httponly_cookie(client):
    client.post(
        "/api/auth/register",
        json={"email": "carol@example.com", "password": "StrongPass123!"},
    )
    res = client.post(
        "/api/auth/login",
        data={"username": "carol@example.com", "password": "StrongPass123!"},
    )
    assert res.status_code == 200
    set_cookie = res.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_login_wrong_password_rejected(client):
    client.post(
        "/api/auth/register",
        json={"email": "dave@example.com", "password": "StrongPass123!"},
    )
    res = client.post(
        "/api/auth/login",
        data={"username": "dave@example.com", "password": "WrongPassword"},
    )
    assert res.status_code == 401


def test_me_works_from_cookie_alone(auth_client):
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "user@example.com"


def test_me_requires_auth(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_logout_clears_cookie_and_revokes_access(auth_client):
    res = auth_client.post("/api/auth/logout")
    assert res.status_code == 200

    res = auth_client.get("/api/auth/me")
    assert res.status_code == 401
