"""Tests for clinical medical record extraction and NLP inquiry parsing."""

import pytest
from fastapi.testclient import TestClient
from medvoyage.api import app
from medvoyage.extractor import extract_clinical_inquiry
from medvoyage.models import Urgency

client = TestClient(app)


def test_clinical_discharge_summary_extraction():
    sample_clinical_note = """
    DISCHARGE SUMMARY / REFERRAL
    Patient Name: David Henderson
    Age: 58 years old
    Gender: Male
    Country of Residence: Canada
    
    Clinical Assessment:
    Patient presents with severe left knee gonarthrosis and tricompartmental osteoarthritis.
    Weight-bearing radiograph demonstrates complete joint space collapse and subchondral sclerosis.
    Conservative management including corticosteroid injections has failed.
    Indication for elective total knee arthroplasty (TKA).
    
    Comorbidities: Essential Hypertension, controlled.
    Current Medications: Lisinopril 20mg daily, Aspirin 81mg (anticoagulant).
    Urgency: Routine surgical candidate, seeks treatment within the next 4 to 6 weeks.
    """

    extracted = extract_clinical_inquiry(sample_clinical_note)
    assert extracted.patient_name == "David Henderson"
    assert extracted.patient_age == 58
    assert extracted.patient_gender == "Male"
    assert extracted.patient_country == "Canada"
    assert extracted.matched_treatment_id == "knee-replacement"
    assert extracted.category == "Orthopedics"
    assert extracted.urgency == Urgency.WITHIN_MONTH
    assert extracted.recommended_budget_usd == 16000.0
    assert "Hypertension" in extracted.comorbidities
    assert any("anticoagulant" in alert.lower() for alert in extracted.surgical_alerts)


def test_cardiac_cabg_emergency_extraction():
    cardiac_note = """
    CARDIAC CATHETERIZATION REPORT
    Patient: Arthur Pendelton
    Age: 64 yo Male
    Diagnosis: Severe triple vessel coronary artery disease with critical 90% proximal LAD stenosis.
    Patient experiencing unstable angina on minimal exertion.
    Urgent indication for off-pump coronary artery bypass graft (CABG) surgery.
    """
    extracted = extract_clinical_inquiry(cardiac_note)
    assert extracted.matched_treatment_id == "cabg-cardiac"
    assert extracted.category == "Cardiology"
    assert extracted.urgency == Urgency.URGENT
    assert extracted.recommended_budget_usd == 24000.0


def test_api_extract_records_endpoint():
    res = client.post(
        "/api/inquiries/extract-records",
        json={
            "medical_records_text": "Patient Name: Maria Santos, 49yo female from USA. Severe periodontitis and fully edentulous lower arch requiring All-on-4 dental implants."
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["matched_treatment_id"] == "dental-all-on-4"
    assert data["patient_name"] == "Maria Santos"
    assert data["patient_age"] == 49
    assert data["patient_gender"] == "Female"
    assert data["patient_country"] == "USA"
    assert data["ready_for_inquiry"] is True


def test_extractor_handles_suffering_from_symptoms_without_country_false_positive():
    """Verify that 'suffering from acute knee pain' does NOT extract 'acute knee pain' as country."""
    text = """
    Patient Name: Arthur Dent
    Age: 42
    Gender: Male
    Suffering from acute pain in right knee and severe osteoarthritis.
    """
    res = extract_clinical_inquiry(text)
    assert res.patient_country != "acute pain in right knee"
    assert res.patient_country == "United States"  # safe default
    assert res.patient_age == 42
    assert res.patient_gender == "Male"


def test_extractor_handles_explicit_gender_with_family_history_she():
    """Verify that a male patient with 'Gender: Male' is not marked Female due to 'she' in family history."""
    text = """
    Patient Name: John Doe
    55yo
    Gender: Male
    Family history: Mother had diabetes before she passed away.
    Assessment: Severe hip osteoarthritis, candidate for anterior hip replacement.
    """
    res = extract_clinical_inquiry(text)
    assert res.patient_gender == "Male"
    assert res.patient_age == 55
    assert res.matched_treatment_id == "hip-replacement"
