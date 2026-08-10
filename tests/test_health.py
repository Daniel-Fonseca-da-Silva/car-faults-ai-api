async def test_health_returns_ok(async_client):
    response = await async_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Auto Crónica AI API"
    assert "version" in body


async def test_health_requires_no_auth(async_client):
    response = await async_client.get("/health")

    assert response.status_code == 200
