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


def test_web_ui_routes_coverage():
    # 1. Treatments Catalog & Detail
    r_t = client.get("/treatments")
    assert r_t.status_code == 200
    assert "Comprehensive Treatment Catalogue" in r_t.text

    r_td = client.get("/treatments/knee-replacement")
    assert r_td.status_code == 200
    assert "Procedure Description" in r_td.text

    # 2. Destinations & Detail
    r_d = client.get("/destinations")
    assert r_d.status_code == 200
    assert "Accredited Medical Tourism Destinations" in r_d.text

    r_dd = client.get("/destinations/uae-abu-dhabi")
    assert r_dd.status_code == 200
    assert "Abu Dhabi Healthcare Guide" in r_dd.text

    # 3. Providers & Detail
    r_p = client.get("/providers")
    assert r_p.status_code == 200
    assert "Verified Doctors & Partner Hospitals" in r_p.text

    r_pd = client.get("/providers/prov-ramesh-apollo")
    assert r_pd.status_code == 200
    assert "Board Certifications" in r_pd.text

    # 4. Compare Quotes
    r_c = client.get("/compare?treatment=knee-replacement")
    assert r_c.status_code == 200
    assert "Itemized Procedure Quote Comparison" in r_c.text

    # 5. Inquiry New & Records Upload
    r_inq = client.get("/inquiry/new")
    assert r_inq.status_code == 200
    assert "Create Medical Case" in r_inq.text

    r_up = client.get("/records/upload")
    assert r_up.status_code == 200
    assert "Discharge Summary & Record Parser" in r_up.text

    # 6. Referral & Help Pages
    r_ref = client.get("/referral")
    assert r_ref.status_code == 200
    assert "5% Commission" in r_ref.text

    r_hlp = client.get("/help")
    assert r_hlp.status_code == 200
    assert "Help Centre" in r_hlp.text

    # 7. Provider Portal CRM & Analytics
    r_lead = client.get("/portal/leads")
    assert r_lead.status_code == 200
    assert "Incoming International Patient Leads" in r_lead.text

    r_qb = client.get("/portal/quote/new")
    assert r_qb.status_code == 200
    assert "Generate Transparent Surgical Proposal" in r_qb.text

    r_an = client.get("/portal/analytics")
    assert r_an.status_code == 200
    assert "Executive CRM Analytics Dashboard" in r_an.text
