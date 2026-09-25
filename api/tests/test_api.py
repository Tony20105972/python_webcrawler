from fastapi.testclient import TestClient

from api.main import app


def test_rejects_local_url_before_fetching():
    response = TestClient(app).post("/api/extract", json={"url": "http://127.0.0.1/private"})
    assert response.status_code == 400
    assert "internal" in response.json()["detail"].lower() or "private" in response.json()["detail"].lower()


def test_rejects_non_http_url():
    response = TestClient(app).post("/api/extract", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422
