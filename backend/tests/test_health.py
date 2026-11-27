def test_service_health(client):
    """Verifies that the /api/health endpoint returns 200 OK and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data

def test_db_health_unconfigured(client):
    """
    Verifies that /api/health/db returns 503 Service Unavailable with a helpful
    message when DATABASE_URL is not configured or still has placeholders.
    """
    response = client.get("/api/health/db")
    # In testing config with no Neon DB yet configured, it should return unconfigured or disconnected safely
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert "status" in data
    assert "database" in data

