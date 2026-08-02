import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_and_list_chat_sessions():
    # 1. Create a session
    create_res = client.post("/api/v1/chat/new", json={"title": "Test Session"})
    assert create_res.status_code == 201
    session_data = create_res.json()
    assert "id" in session_data
    assert session_data["title"] == "Test Session"
    session_id = session_data["id"]

    # 2. List sessions
    list_res = client.get("/api/v1/chat")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert any(s["id"] == session_id for s in sessions)

    # 3. Post a message
    msg_res = client.post(
        f"/api/v1/chat/{session_id}/message",
        json={"role": "user", "content": "Hello Lenny Assistant"},
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["content"] == "Hello Lenny Assistant"

    # 4. Get session detail with messages
    detail_res = client.get(f"/api/v1/chat/{session_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["messages"]) >= 1
    assert detail["messages"][0]["content"] == "Hello Lenny Assistant"

    # 5. Rename session
    patch_res = client.patch(
        f"/api/v1/chat/{session_id}", json={"title": "Renamed Session"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Renamed Session"

    # 6. Delete session
    del_res = client.delete(f"/api/v1/chat/{session_id}")
    assert del_res.status_code == 204
