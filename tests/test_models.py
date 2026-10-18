"""Tests for MedVoyage data models."""

from medvoyage.models import Destination, ItemizedQuote, PatientInquiry, Provider, Treatment, Urgency


def test_patient_inquiry_creation():
    inq = PatientInquiry(
        patient_name="John Doe",
        patient_email="john@example.com",
        patient_country="USA",
        treatment_id="knee-replacement",
        budget_usd=15000.0,
        urgency=Urgency.URGENT,
        medical_records_summary="Knee pain",
    )
    assert inq.patient_name == "John Doe"
    assert inq.urgency == Urgency.URGENT
    assert inq.id.startswith("inq-")


def test_quote_model_integrity():
    quote = ItemizedQuote(
        provider_id="p1",
        provider_name="Dr. Test",
        hospital_id="h1",
        hospital_name="Hospital Test",
        treatment_name="Knee Replacement",
        country="India",
        base_procedure_usd=4000.0,
        surgeon_fee_usd=2000.0,
        facility_stay_usd=1500.0,
        anesthesia_meds_usd=800.0,
        total_package_usd=8300.0,
        included_services=["Private Room", "Surgeon Fee"],
        disclosed_additional_expenses=["Extra Nights"],
        consultation_availability="Daily",
        estimated_waiting_days=4,
        aftercare_arrangements="14 days follow-up",
        provider_qualifications_summary="FRCS",
    )
    assert quote.total_package_usd == 8300.0
    assert len(quote.included_services) == 2
    assert len(quote.disclosed_additional_expenses) == 1
