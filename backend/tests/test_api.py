from fastapi.testclient import TestClient

from backend.app.main import app


def test_measurements_endpoint_returns_dashboard_payload():
    client = TestClient(app)
    response = client.get("/api/measurements?city=Recife&country=BR&parameter=pm25&days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["city"] == "Recife"
    assert len(payload["series"]) == 30
    assert len(payload["stations"]) > 0
    assert payload["metrics"]["average"] > 0
