"""Tests for API Key authentication on MedVoyage endpoints."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from medvoyage.api import app

client = TestClient(app)


def test_api_key_security_on_medvoyage(monkeypatch):
    # Health endpoint is public
    health_res = client.get("/health")
    assert health_res.status_code == 200

    # In dev mode (unconfigured key), inquiry submission proceeds
    monkeypatch.delenv("MEDVOYAGE_API_KEY", raising=False)
    inq_payload = {
        "patient_name": "Dev User",
        "patient_email": "dev@example.com",
        "patient_country": "USA",
        "treatment_id": "knee-replacement",
        "budget_usd": 15000.0,
        "medical_records_summary": "Knee OA",
    }
    dev_res = client.post("/api/inquiries", json=inq_payload)
    assert dev_res.status_code == 200

    # Enforce API key in production mode
    secret = "medvoyage-secure-key-99"
    monkeypatch.setenv("MEDVOYAGE_API_KEY", secret)

    # Missing header -> 401
    blocked_res = client.post("/api/inquiries", json=inq_payload)
    assert blocked_res.status_code == 401
    assert "Invalid or missing X-API-Key" in blocked_res.json()["detail"]

    # Wrong key -> 401
    bad_key_res = client.post(
        "/api/inquiries",
        headers={"X-API-Key": "wrong-key"},
        json=inq_payload,
    )
    assert bad_key_res.status_code == 401

    # Valid key -> 200
    ok_res = client.post(
        "/api/inquiries",
        headers={"X-API-Key": secret},
        json=inq_payload,
    )
    assert ok_res.status_code == 200
