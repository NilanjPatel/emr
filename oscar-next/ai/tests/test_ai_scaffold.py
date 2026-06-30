"""Tests for the AI sidecar application scaffold."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client):
    with patch("app.main.ollama_client.is_available", new_callable=AsyncMock, return_value=False):
        async with client as c:
            r = await c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["suggestion_only"] is True
    assert "ollama" in body
    assert "anthropic" in body


@pytest.mark.asyncio
async def test_health_shows_ollama_unavailable(client):
    with patch("app.main.ollama_client.is_available", new_callable=AsyncMock, return_value=False):
        async with client as c:
            r = await c.get("/health")
    assert r.json()["ollama"] == "unavailable"


@pytest.mark.asyncio
async def test_health_shows_ollama_available(client):
    with patch("app.main.ollama_client.is_available", new_callable=AsyncMock, return_value=True):
        async with client as c:
            r = await c.get("/health")
    assert r.json()["ollama"] == "available"


@pytest.mark.asyncio
async def test_encounter_assist_503_when_ollama_down(client):
    with patch("app.routers.encounter.ollama_client.is_available", new_callable=AsyncMock, return_value=False):
        async with client as c:
            r = await c.post("/ai/encounter-assist", json={"transcript": "patient has cough"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_encounter_assist_returns_suggestion(client):
    with (
        patch("app.routers.encounter.ollama_client.is_available", new_callable=AsyncMock, return_value=True),
        patch("app.routers.encounter.ollama_client.complete", new_callable=AsyncMock, return_value="Subjective: patient reports cough"),
    ):
        async with client as c:
            r = await c.post("/ai/encounter-assist", json={"transcript": "patient has cough", "section": "S"})
    assert r.status_code == 200
    body = r.json()
    assert "suggestion" in body
    assert body["model"] == "ollama"
    assert body["section"] == "S"


@pytest.mark.asyncio
async def test_summarize_patient_503_when_no_api_key(client):
    with patch("app.routers.summarize.anthropic_client.complete", new_callable=AsyncMock, side_effect=RuntimeError("ANTHROPIC_API_KEY not configured")):
        async with client as c:
            r = await c.post("/ai/summarize-patient", json={"patient_history": "John Smith, DOB 1970-01-01, has hypertension"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_summarize_deidentifies_before_sending(client):
    captured = {}

    async def mock_complete(system, prompt, max_tokens=None):
        captured["prompt"] = prompt
        return "Summary of patient with hypertension"

    with patch("app.routers.summarize.anthropic_client.complete", side_effect=mock_complete):
        async with client as c:
            r = await c.post("/ai/summarize-patient", json={
                "patient_history": "Patient DOB 1970-01-01, email john@test.com, has hypertension"
            })

    assert r.status_code == 200
    assert "john@test.com" not in captured.get("prompt", "")
    assert "1970-01-01" not in captured.get("prompt", "")
    body = r.json()
    assert body["phi_replacements"] >= 2


@pytest.mark.asyncio
async def test_drug_interaction_requires_medications(client):
    with patch("app.routers.cds.ollama_client.is_available", new_callable=AsyncMock, return_value=True):
        async with client as c:
            r = await c.post("/ai/drug-interaction", json={"medications": []})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_drug_interaction_returns_result(client):
    with (
        patch("app.routers.cds.ollama_client.is_available", new_callable=AsyncMock, return_value=True),
        patch("app.routers.cds.ollama_client.complete", new_callable=AsyncMock, return_value="No significant interactions"),
    ):
        async with client as c:
            r = await c.post("/ai/drug-interaction", json={"medications": ["metformin", "lisinopril"]})
    assert r.status_code == 200
    assert r.json()["interactions"] == "No significant interactions"


@pytest.mark.asyncio
async def test_suggest_codes_deidentifies(client):
    captured = {}

    async def mock_complete(system, prompt, max_tokens=None):
        captured["prompt"] = prompt
        return "Z00.00 - General adult medical examination"

    with patch("app.routers.billing.anthropic_client.complete", side_effect=mock_complete):
        async with client as c:
            r = await c.post("/ai/suggest-codes", json={
                "encounter_note": "Patient Jane DOB 1985-03-15, email jane@test.com. Annual physical."
            })

    assert r.status_code == 200
    assert "jane@test.com" not in captured.get("prompt", "")
    assert r.json()["province"] == "ON"


@pytest.mark.asyncio
async def test_cds_alerts_returns_alerts(client):
    with (
        patch("app.routers.cds.ollama_client.is_available", new_callable=AsyncMock, return_value=True),
        patch("app.routers.cds.ollama_client.complete", new_callable=AsyncMock, return_value="- Colorectal cancer screening overdue"),
    ):
        async with client as c:
            r = await c.post("/ai/cds-alerts", json={
                "age": 52,
                "sex": "M",
                "conditions": ["hypertension"],
                "preventions": ["influenza_2024"]
            })
    assert r.status_code == 200
    assert "alerts" in r.json()


@pytest.mark.asyncio
async def test_openapi_schema_available(client):
    async with client as c:
        r = await c.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    routes = [r["operationId"] for r in schema["paths"].values() for r in r.values()]
    assert any("encounter" in op for op in routes)
