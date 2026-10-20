"""Tests for SQLite persistence in MedVoyage marketplace."""

from datetime import datetime, timezone
import pytest
from medvoyage.models import AftercareMilestone, ConsultationBooking, PatientInquiry, Urgency
from medvoyage.storage import SQLiteMedVoyageStorage


def test_sqlite_persistence_lifecycle(tmp_path):
    db_file = tmp_path / "test_medvoyage.db"
    storage1 = SQLiteMedVoyageStorage(db_file)

    # 1. Save Patient Inquiry
    inq = PatientInquiry(
        id="INQ-SQL-1",
        patient_name="Robert Taylor",
        patient_email="robert@example.com",
        patient_country="United Kingdom",
        treatment_id="knee-replacement",
        budget_usd=18000.0,
        preferred_destinations=["india-chennai", "thailand-bangkok"],
        urgency=Urgency.WITHIN_MONTH,
        medical_records_summary="Bilateral knee osteoarthrosis stage 4",
    )
    storage1.save_inquiry(inq)

    # 2. Save Booking
    t0 = datetime(2026, 11, 15, 14, 0, tzinfo=timezone.utc)
    booking = ConsultationBooking(
        booking_id="BK-SQL-1",
        inquiry_id="INQ-SQL-1",
        provider_id="prov-ramesh-apollo",
        scheduled_at=t0,
        consultation_type="telehealth_video",
        notes="Pre-op consult",
    )
    storage1.save_booking(booking)

    # 3. Save Aftercare Milestones
    m1 = AftercareMilestone(
        id="AFT-01",
        booking_id="BK-SQL-1",
        day_post_op=1,
        title="Inpatient Mobility Assessment",
        instructions="Physical therapy bedside assessment",
    )
    m2 = AftercareMilestone(
        id="AFT-02",
        booking_id="BK-SQL-1",
        day_post_op=14,
        title="Fit-to-fly teleconsultation",
        instructions="Range of motion validation",
        telehealth_checkin_required=True,
    )
    storage1.save_aftercare_milestones("BK-SQL-1", [m1, m2])

    # Disconnect and open with second storage instance
    storage2 = SQLiteMedVoyageStorage(db_file)

    loaded_inq = storage2.get_inquiry("INQ-SQL-1")
    assert loaded_inq is not None
    assert loaded_inq.patient_name == "Robert Taylor"
    assert loaded_inq.budget_usd == 18000.0

    loaded_bk = storage2.get_booking("BK-SQL-1")
    assert loaded_bk is not None
    assert loaded_bk.provider_id == "prov-ramesh-apollo"

    loaded_milestones = storage2.get_aftercare_milestones("BK-SQL-1")
    assert len(loaded_milestones) == 2
    assert loaded_milestones[0].id == "AFT-01"
    assert not loaded_milestones[0].is_completed

    # Complete milestone in instance 2
    completed = storage2.complete_aftercare_milestone("BK-SQL-1", "AFT-01")
    assert completed is True

    # Verify instance 3 reflects completion
    storage3 = SQLiteMedVoyageStorage(db_file)
    updated_milestones = storage3.get_aftercare_milestones("BK-SQL-1")
    assert updated_milestones[0].is_completed is True
