"""Tests for consultation bookings and continuous aftercare tracker."""

from datetime import datetime, timedelta, timezone
from medvoyage.aftercare import AFTERCARE_MANAGER
from medvoyage.booking import BOOKING_MANAGER


def test_booking_and_aftercare_generation():
    t0 = datetime.now(timezone.utc)
    booking = BOOKING_MANAGER.create_booking(
        inquiry_id="inq-123",
        provider_id="prov-tariq-ccad",
        scheduled_at=t0 + timedelta(days=3),
        consultation_type="telehealth_video",
        notes="Pre-travel consultation",
    )
    assert booking.status == "CONFIRMED"
    assert booking.booking_id.startswith("bk-")

    # Generate aftercare plan
    plan = AFTERCARE_MANAGER.generate_plan(booking.booking_id, treatment_category="Orthopedics")
    assert len(plan) == 6
    assert plan[0].day_post_op == 1
    assert any(m.telehealth_checkin_required for m in plan)

    # Complete a milestone
    milestone_id = plan[0].id
    assert not plan[0].is_completed
    ok = AFTERCARE_MANAGER.complete_milestone(booking.booking_id, milestone_id)
    assert ok is True
    assert plan[0].is_completed is True
