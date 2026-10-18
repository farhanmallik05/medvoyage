"""Consultation booking and scheduling manager for MedVoyage."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from medvoyage.catalog import get_provider_by_id
from medvoyage.models import ConsultationBooking


class BookingManager:
    def __init__(self):
        self._bookings: Dict[str, ConsultationBooking] = {}

    def create_booking(
        self,
        inquiry_id: str,
        provider_id: str,
        scheduled_at: datetime,
        consultation_type: str = "telehealth_video",
        notes: Optional[str] = None,
    ) -> ConsultationBooking:
        provider = get_provider_by_id(provider_id)
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        booking = ConsultationBooking(
            inquiry_id=inquiry_id,
            provider_id=provider_id,
            scheduled_at=scheduled_at,
            consultation_type=consultation_type,
            status="CONFIRMED",
            notes=notes,
        )
        self._bookings[booking.booking_id] = booking
        return booking

    def get_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        return self._bookings.get(booking_id)

    def list_bookings(self) -> List[ConsultationBooking]:
        return list(self._bookings.values())


BOOKING_MANAGER = BookingManager()
