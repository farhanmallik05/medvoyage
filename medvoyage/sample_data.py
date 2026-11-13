"""Sample data seeder for MedVoyage platform."""

from datetime import datetime, timedelta, timezone
from medvoyage.aftercare import AFTERCARE_MANAGER
from medvoyage.booking import BOOKING_MANAGER
from medvoyage.models import (
    LeadStatus,
    Notification,
    PatientCase,
    PatientInquiry,
    ProviderReview,
    ReferralRecord,
    Urgency,
)


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


def seed_sample_reviews():
    return [
        ProviderReview(
            id="rev-1",
            provider_id="prov-ramesh-apollo",
            patient_name="Sarah Miller",
            patient_country="United Kingdom",
            treatment_name="Total Knee Replacement (Minimally Invasive)",
            rating=5.0,
            comment="Dr. Ramesh and the Apollo international concierge were extraordinary. The total package was $8,360 compared to £18,000 in London private hospitals. Walking unassisted after 3 weeks!",
            verified_patient=True,
        ),
        ProviderReview(
            id="rev-2",
            provider_id="prov-ramesh-apollo",
            patient_name="Michael O'Connor",
            patient_country="Ireland",
            treatment_name="Anterior Hip Replacement",
            rating=4.9,
            comment="Zero hidden expenses. Everything from the airport transfer to the post-op physical therapy was covered exactly as itemized in the quote.",
            verified_patient=True,
        ),
        ProviderReview(
            id="rev-3",
            provider_id="prov-tariq-ccad",
            patient_name="James Henderson",
            patient_country="United States",
            treatment_name="Total Knee Replacement (Minimally Invasive)",
            rating=5.0,
            comment="Cleveland Clinic Abu Dhabi feels like a 5-star resort combined with Johns Hopkins. Dr. Tariq explained every nuance over telehealth before I even booked my flight.",
            verified_patient=True,
        ),
        ProviderReview(
            id="rev-4",
            provider_id="prov-somchai-bumrungrad",
            patient_name="Chloe Dubois",
            patient_country="France",
            treatment_name="All-on-4 Full Arch Dental Implants",
            rating=4.9,
            comment="Bumrungrad's hospitality and dental surgery standards are world-class. Saved over 65% with complete clarity on medication and stay.",
            verified_patient=True,
        ),
    ]


def seed_sample_referrals():
    return [
        ReferralRecord(
            id="ref-101",
            referrer_name="Dr. Andrew Collins, MD",
            referrer_type="Doctor / General Practitioner",
            referrer_email="acollins@londonhealth.org",
            patient_name="David Thompson",
            booking_id="bk-sample-cabg",
            billed_amount_usd=26400.0,
            commission_pct=5.0,
            commission_earned_usd=1320.0,
            status="APPROVED",
        ),
        ReferralRecord(
            id="ref-102",
            referrer_name="Harborview Physical Therapy Clinic",
            referrer_type="Clinic Partner",
            referrer_email="intake@harborviewpt.com",
            patient_name="Robert Jenkins",
            booking_id="bk-sample-knee",
            billed_amount_usd=8360.0,
            commission_pct=5.0,
            commission_earned_usd=418.0,
            status="PAID",
        ),
    ]


def seed_sample_notifications():
    return [
        Notification(
            id="notif-1",
            recipient="patient",
            title="Telehealth Consultation Confirmed",
            message="Your video consultation with Dr. Ramesh Sundaram is confirmed for in 2 days at 10:00 AM IST.",
            category="booking",
            is_read=False,
        ),
        Notification(
            id="notif-2",
            recipient="provider",
            title="New Medical Inquiry Received",
            message="Robert Jenkins submitted clinical discharge records for Total Knee Replacement consideration.",
            category="inquiry",
            is_read=False,
        ),
        Notification(
            id="notif-3",
            recipient="provider",
            title="Transparent Quote Viewed",
            message="David Thompson reviewed your itemized CABG surgical proposal.",
            category="quote",
            is_read=True,
        ),
    ]


    return [inq1, inq2]
