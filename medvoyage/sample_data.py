"""Sample data seeder for MedVoyage platform."""

from datetime import datetime, timedelta, timezone
from medvoyage.aftercare import AFTERCARE_MANAGER
from medvoyage.booking import BOOKING_MANAGER
from medvoyage.models import PatientInquiry, Urgency


def seed_sample_marketplace_data():
    t0 = datetime.now(timezone.utc)

    # 1. Patient inquiry from US looking for affordable knee replacement
    inq1 = PatientInquiry(
        id="inq-sample-knee",
        patient_name="Robert Jenkins",
        patient_email="robert.jenkins@example.com",
        patient_country="United States",
        treatment_id="knee-replacement",
        budget_usd=12000.0,
        preferred_destinations=["India", "Thailand"],
        urgency=Urgency.WITHIN_MONTH,
        preferred_language="en",
        medical_records_summary="Bilateral severe osteoarthritis grade 4; previous arthroscopy 2024; ambulatory with cane.",
    )

    # 2. Patient inquiry from UK looking for CABG
    inq2 = PatientInquiry(
        id="inq-sample-cabg",
        patient_name="David Thompson",
        patient_email="david.t@example.co.uk",
        patient_country="United Kingdom",
        treatment_id="cabg-cardiac",
        budget_usd=30000.0,
        preferred_destinations=["United Arab Emirates", "India"],
        urgency=Urgency.URGENT,
        preferred_language="en",
        medical_records_summary="Triple vessel coronary artery disease; NHS waitlist exceeding 14 months; ejection fraction 50%.",
    )

    # Seed an active confirmed consultation booking
    booking = BOOKING_MANAGER.create_booking(
        inquiry_id="inq-sample-knee",
        provider_id="prov-ramesh-apollo",
        scheduled_at=t0 + timedelta(days=2),
        consultation_type="telehealth_video",
        notes="Patient inquiring about computer navigation technique and implant alloy options.",
    )

    # Seed aftercare plan
    AFTERCARE_MANAGER.generate_plan(booking.booking_id, treatment_category="Orthopedics")

    return [inq1, inq2]
