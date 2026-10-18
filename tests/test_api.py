"""Tests for MedVoyage REST API endpoints."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from medvoyage.api import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "MedVoyage Marketplace"


def test_catalog_endpoints():
    d_res = client.get("/api/destinations")
    assert d_res.status_code == 200
    assert len(d_res.json()) >= 4

    t_res = client.get("/api/treatments")
    assert t_res.status_code == 200
    assert len(t_res.json()) >= 4

    p_res = client.get("/api/providers")
    assert p_res.status_code == 200
    assert len(p_res.json()) >= 4


def test_quote_comparison_endpoint():
    res = client.get("/api/quotes/compare?treatment_id=knee-replacement")
    assert res.status_code == 200
    quotes = res.json()
    assert len(quotes) >= 3
    assert "total_package_usd" in quotes[0]
    assert "disclosed_additional_expenses" in quotes[0]


def test_inquiry_and_matching_flow():
    inquiry_payload = {
        "patient_name": "Test User",
        "patient_email": "test@user.com",
        "patient_country": "Canada",
        "treatment_id": "knee-replacement",
        "budget_usd": 15000.0,
        "preferred_destinations": ["India", "Thailand"],
        "urgency": "WITHIN_MONTH",
        "preferred_language": "en",
        "medical_records_summary": "Test records",
    }
    create_res = client.post("/api/inquiries", json=inquiry_payload)
    assert create_res.status_code == 200
    inquiry_obj = create_res.json()

    # Match providers
    match_res = client.post("/api/match", json=inquiry_obj)
    assert match_res.status_code == 200
    matches = match_res.json()
    assert len(matches) > 0
    assert "total_score" in matches[0]


def test_marketplace_html_homepage():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "MedVoyage" in res.text
