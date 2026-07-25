VALID_PAYLOAD = {
    "targetLanguage": "pt-PT",
    "sourceLanguage": "en-GB",
    "knownIssues": [
        {
            "title": "Gearbox synchro wear",
            "description": "Synchros wear out prematurely under normal use.",
            "severity": "high",
            "typicalKm": 120000,
            "sources": ["VW owner forums"],
            "fixes": [
                {
                    "summary": "Replace gearbox synchros",
                    "steps": "Remove gearbox, replace synchro rings, reassemble.",
                    "estimatedCostEur": 450,
                }
            ],
        }
    ],
}


async def test_translate_without_auth_header_returns_401(async_client):
    response = await async_client.post("/translate", json=VALID_PAYLOAD)

    assert response.status_code == 401


async def test_translate_with_wrong_key_returns_401(async_client):
    response = await async_client.post(
        "/translate",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer wrong-key"},
    )

    assert response.status_code == 401


async def test_translate_with_invalid_body_returns_422(async_client, auth_headers):
    response = await async_client.post(
        "/translate",
        json={"targetLanguage": "pt-PT"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_translate_with_unknown_language_returns_422(async_client, auth_headers):
    payload = {**VALID_PAYLOAD, "targetLanguage": "fr-FR"}

    response = await async_client.post("/translate", json=payload, headers=auth_headers)

    assert response.status_code == 422


async def test_translate_with_valid_request_returns_stub_result(
    async_client, auth_headers
):
    response = await async_client.post(
        "/translate", json=VALID_PAYLOAD, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()

    assert len(body["knownIssues"]) == 1
    issue = body["knownIssues"][0]
    assert issue["title"] == "[pt-PT] Gearbox synchro wear"
    assert (
        issue["description"]
        == "[pt-PT] Synchros wear out prematurely under normal use."
    )
    assert issue["severity"] == "high"
    assert issue["typicalKm"] == 120000
    assert issue["sources"] == ["VW owner forums"]
    assert len(issue["fixes"]) == 1
    fix = issue["fixes"][0]
    assert fix["summary"] == "[pt-PT] Replace gearbox synchros"
    assert fix["steps"] == "[pt-PT] Remove gearbox, replace synchro rings, reassemble."
    assert fix["estimatedCostEur"] == 450


async def test_translate_preserves_known_issue_and_fix_count(
    async_client, auth_headers
):
    payload = {
        **VALID_PAYLOAD,
        "knownIssues": [
            *VALID_PAYLOAD["knownIssues"],
            {
                "title": "Rust on wheel arches",
                "description": "Wheel arches corrode over time.",
                "severity": "low",
                "fixes": [],
            },
        ],
    }

    response = await async_client.post("/translate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["knownIssues"]) == 2
    assert body["knownIssues"][1]["title"] == "[pt-PT] Rust on wheel arches"
    assert body["knownIssues"][1]["fixes"] == []
