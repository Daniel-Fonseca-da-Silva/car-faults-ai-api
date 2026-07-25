VALID_PAYLOAD = {
    "brand": "Volkswagen",
    "model": "Polo",
    "year": 2015,
    "engine": "1.2 TSI",
    "fuelType": "gasoline",
    "doors": 5,
}


async def test_lookup_without_auth_header_returns_401(async_client):
    response = await async_client.post("/lookup", json=VALID_PAYLOAD)

    assert response.status_code == 401


async def test_lookup_with_wrong_key_returns_401(async_client):
    response = await async_client.post(
        "/lookup",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer wrong-key"},
    )

    assert response.status_code == 401


async def test_lookup_with_invalid_body_returns_422(async_client, auth_headers):
    response = await async_client.post(
        "/lookup",
        json={"brand": "Volkswagen"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_lookup_with_valid_request_returns_stub_result(
    async_client, auth_headers
):
    response = await async_client.post(
        "/lookup",
        json=VALID_PAYLOAD,
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["vehicle"] == {
        "brand": "Volkswagen",
        "model": "Polo",
        "name": "Volkswagen Polo",
        "year": 2015,
        "engine": "1.2 TSI",
        "fuelType": "gasoline",
        "doors": 5,
        "techSpecs": None,
    }
    assert len(body["knownIssues"]) == 1

    issue = body["knownIssues"][0]
    assert issue["title"] == "Stub known issue"
    assert issue["severity"] == "medium"
    assert len(issue["fixes"]) == 1
    assert issue["fixes"][0]["summary"] == "Stub fix"


async def test_lookup_without_optional_doors(async_client, auth_headers):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "doors"}

    response = await async_client.post("/lookup", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["vehicle"]["doors"] is None


async def test_lookup_without_required_fuel_type_returns_422(
    async_client, auth_headers
):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "fuelType"}

    response = await async_client.post("/lookup", json=payload, headers=auth_headers)

    assert response.status_code == 422


async def test_lookup_with_unknown_fuel_type_returns_422(async_client, auth_headers):
    payload = {**VALID_PAYLOAD, "fuelType": "kerosene"}

    response = await async_client.post("/lookup", json=payload, headers=auth_headers)

    assert response.status_code == 422


async def test_lookup_without_language_defaults_to_en_gb(async_client, auth_headers):
    response = await async_client.post(
        "/lookup", json=VALID_PAYLOAD, headers=auth_headers
    )

    assert response.status_code == 200


async def test_lookup_with_explicit_language_returns_200(async_client, auth_headers):
    payload = {**VALID_PAYLOAD, "language": "pt-PT"}

    response = await async_client.post("/lookup", json=payload, headers=auth_headers)

    assert response.status_code == 200


async def test_lookup_with_unknown_language_returns_422(async_client, auth_headers):
    payload = {**VALID_PAYLOAD, "language": "fr-FR"}

    response = await async_client.post("/lookup", json=payload, headers=auth_headers)

    assert response.status_code == 422
