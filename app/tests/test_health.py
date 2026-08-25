from fastapi.testclient import TestClient
from application import create_app


def test_health_endpoint():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["role"] == "a2a_client_server"
        assert data["supervisor_active"] is True
