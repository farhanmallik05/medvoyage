"""Tests for MedVoyage AI provider matching engine."""

from medvoyage.matcher import match_providers_for_inquiry
from medvoyage.models import PatientInquiry, Urgency


def test_matching_ranks_providers_intelligently():
    # Inquiry with tight budget for knee replacement
    inq = PatientInquiry(
        patient_name="Budget Patient",
        patient_email="budget@example.com",
        patient_country="USA",
        treatment_id="knee-replacement",
        budget_usd=10000.0,
        preferred_destinations=["India"],
        urgency=Urgency.WITHIN_MONTH,
        preferred_language="en",
        medical_records_summary="Knee osteoarthritis",
    )
    matches = match_providers_for_inquiry(inq)
    assert len(matches) > 0
    # Top match should be within budget and in India (Dr. Ramesh Sundaram at Apollo)
    top = matches[0]
    assert top.country == "India"
    assert top.estimated_quote_usd <= inq.budget_usd
    assert top.total_score >= 80.0


def test_matching_adapts_to_urgent_premium_preference():
    inq = PatientInquiry(
        patient_name="Premium Patient",
        patient_email="vip@example.com",
        patient_country="UK",
        treatment_id="knee-replacement",
        budget_usd=25000.0,
        preferred_destinations=["United Arab Emirates"],
        urgency=Urgency.URGENT,
        preferred_language="en",
        medical_records_summary="Severe cartilage loss",
    )
    matches = match_providers_for_inquiry(inq)
    top = matches[0]
    # UAE provider should rank top for UAE destination preference and high budget
    assert top.country == "United Arab Emirates"
    assert top.total_score > 85.0
