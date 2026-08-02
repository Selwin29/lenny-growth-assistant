import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_and_get_me():
    # 1. Login with a test email
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test-auth@example.com", "full_name": "Test Auth User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test-auth@example.com"
    token = data["access_token"]

    # 2. Access protected endpoint /me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "test-auth@example.com"
    assert me_data["full_name"] == "Test Auth User"

def test_unauthenticated_protected_endpoint():
    # Attempting to access protected chat APIs without token
    # Wait: in development mode, it falls back to the development user dev@example.com.
    # To test strict unauthenticated rejection, let's mock/override the environment to "production".
    from app.core.config import settings
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "production"
    try:
        response = client.get("/api/v1/chat")
        assert response.status_code == 401
    finally:
        settings.ENVIRONMENT = original_env

def test_user_session_ownership():
    # User 1 registers and creates a session
    res1 = client.post("/api/v1/auth/login", json={"email": "user1@example.com"})
    token1 = res1.json()["access_token"]
    
    sess_res = client.post(
        "/api/v1/chat/new",
        json={"title": "User 1 Chat"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    session_id = sess_res.json()["id"]

    # User 2 registers
    res2 = client.post("/api/v1/auth/login", json={"email": "user2@example.com"})
    token2 = res2.json()["access_token"]

    # User 2 attempts to fetch User 1's session -> should return 403 Forbidden
    fetch_res = client.get(
        f"/api/v1/chat/{session_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert fetch_res.status_code == 403

    # User 2 attempts to rename User 1's session -> 403 Forbidden
    rename_res = client.patch(
        f"/api/v1/chat/{session_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert rename_res.status_code == 403

    # User 2 attempts to delete User 1's session -> 403 Forbidden
    delete_res = client.delete(
        f"/api/v1/chat/{session_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert delete_res.status_code == 403
