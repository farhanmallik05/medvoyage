"""Tests for catalog CSV and JSON schema-based ingestion pipelines."""

import json
from fastapi.testclient import TestClient
from medvoyage.api import app
from medvoyage.catalog import get_provider_by_id, get_treatment_by_id
from medvoyage.ingestion import ingest_providers_csv, ingest_treatments_json

client = TestClient(app)


def test_ingest_treatments_json():
    json_data = json.dumps([
        {
            "id": "lasik-custom-wavefront",
            "category": "Ophthalmology",
            "name": "Custom Wavefront LASIK Eye Surgery",
            "description": "Bladeless topography-guided bilateral excimer laser corneal reshaping.",
            "typical_stay_days": 2,
            "recovery_days": 3,
            "us_benchmark_cost_usd": 4800.0,
        }
    ])
    ingested, errors = ingest_treatments_json(json_data)
    assert len(errors) == 0
    assert len(ingested) == 1
    t = get_treatment_by_id("lasik-custom-wavefront")
    assert t is not None
    assert t.category == "Ophthalmology"
    assert t.us_benchmark_cost_usd == 4800.0


def test_ingest_providers_csv():
    csv_data = """id,name,title,specialty,hospital_id,hospital_name,country,city,years_experience,credentials,languages,rating,verified,successful_cases
prov-elena-acibadem,Dr. Elena Popova,Chief of Refractive Surgery,Ophthalmology,hosp-acibadem-ist,Acibadem Maslak Hospital,Turkey,Istanbul,15,Fellow European Board of Ophthalmology;ESCRS Member,English;Russian;Turkish,4.91,true,1420
"""
    ingested, errors = ingest_providers_csv(csv_data)
    assert len(errors) == 0
    assert len(ingested) == 1
    p = get_provider_by_id("prov-elena-acibadem")
    assert p is not None
    assert p.specialty == "Ophthalmology"
    assert "Russian" in p.languages


def test_catalog_ingest_api_endpoint():
    payload = {
        "entity_type": "treatment",
        "format": "json",
        "content": json.dumps([
            {
                "id": "bariatric-gastric-sleeve",
                "category": "Bariatrics",
                "name": "Laparoscopic Sleeve Gastrectomy",
                "description": "Minimally invasive gastric reduction with stapled calibration.",
                "typical_stay_days": 3,
                "recovery_days": 14,
                "us_benchmark_cost_usd": 22000.0,
            }
        ]),
    }
    res = client.post("/api/catalog/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["ingested_count"] == 1
    assert get_treatment_by_id("bariatric-gastric-sleeve") is not None


def test_catalog_ingestion_persistence_sqlite(tmp_path):
    """Verify that catalog ingestion saves to SQLite and persists across instances."""
    from medvoyage.storage import SQLiteMedVoyageStorage

    db_path = tmp_path / "catalog_test.db"
    storage1 = SQLiteMedVoyageStorage(db_path)

    treatment_json = json.dumps([
        {
            "id": "persisted-spinal-fusion",
            "category": "Spine Surgery",
            "name": "Minimally Invasive Lumbar Spinal Fusion",
            "description": "TLIF procedure with titanium pedicle screws and PEEK cage.",
            "typical_stay_days": 4,
            "recovery_days": 28,
            "us_benchmark_cost_usd": 65000.0,
        }
    ])
    ingested, errors = ingest_treatments_json(treatment_json, storage=storage1)
    assert len(errors) == 0
    assert len(ingested) == 1

    # Disconnect and open with instance 2
    storage2 = SQLiteMedVoyageStorage(db_path)
    stored = storage2.list_treatments()
    found = next((t for t in stored if t.id == "persisted-spinal-fusion"), None)
    assert found is not None
    assert found.category == "Spine Surgery"
    assert found.us_benchmark_cost_usd == 65000.0
