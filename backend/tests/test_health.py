"""Health endpoint tests."""

def test_health_returns_ok(client):
    """Health endpoint returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
