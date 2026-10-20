"""Consultation booking and scheduling manager for MedVoyage with persistent storage integration."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from medvoyage.catalog import get_provider_by_id
from medvoyage.models import ConsultationBooking
from medvoyage.storage import MedVoyageStorage


class BookingManager:
    def __init__(self, storage: Optional[MedVoyageStorage] = None):
        self._storage = storage
        self._bookings: Dict[str, ConsultationBooking] = {}

    def set_storage(self, storage: MedVoyageStorage):
        self._storage = storage

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
        if self._storage:
            self._storage.save_booking(booking)
        else:
            self._bookings[booking.booking_id] = booking
        return booking

    def get_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        if self._storage:
            return self._storage.get_booking(booking_id)
        return self._bookings.get(booking_id)

    def list_bookings(self) -> List[ConsultationBooking]:
        if self._storage:
            return self._storage.list_bookings()
        return list(self._bookings.values())


BOOKING_MANAGER = BookingManager()
