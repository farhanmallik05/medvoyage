from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Dict, List, Optional, Union
from medvoyage.models import (
    AftercareMilestone,
    ConsultationBooking,
    Notification,
    PatientCase,
    PatientInquiry,
    Provider,
    ProviderReview,
    ReferralRecord,
    Treatment,
)


class MedVoyageStorage:
    """Base interface for MedVoyage persistence."""

    def save_inquiry(self, inquiry: PatientInquiry) -> PatientInquiry:
        raise NotImplementedError

    def get_inquiry(self, inquiry_id: str) -> Optional[PatientInquiry]:
        raise NotImplementedError

    def list_inquiries(self) -> List[PatientInquiry]:
        raise NotImplementedError

    def save_booking(self, booking: ConsultationBooking) -> ConsultationBooking:
        raise NotImplementedError

    def get_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        raise NotImplementedError

    def list_bookings(self) -> List[ConsultationBooking]:
        raise NotImplementedError

    def save_aftercare_milestones(
        self, booking_id: str, milestones: List[AftercareMilestone]
    ) -> List[AftercareMilestone]:
        raise NotImplementedError

    def get_aftercare_milestones(self, booking_id: str) -> List[AftercareMilestone]:
        raise NotImplementedError

    def complete_aftercare_milestone(self, booking_id: str, milestone_id: str) -> bool:
        raise NotImplementedError

    def save_treatment(self, treatment: Treatment) -> Treatment:
        raise NotImplementedError

    def list_treatments(self) -> List[Treatment]:
        raise NotImplementedError

    def save_provider(self, provider: Provider) -> Provider:
        raise NotImplementedError

    def list_providers(self) -> List[Provider]:
        raise NotImplementedError

    def save_case(self, case: PatientCase) -> PatientCase:
        raise NotImplementedError

    def get_case(self, case_id: str) -> Optional[PatientCase]:
        raise NotImplementedError

    def list_cases(self) -> List[PatientCase]:
        raise NotImplementedError

    def update_case_status(self, case_id: str, status: str, notes: Optional[str] = None) -> bool:
        raise NotImplementedError

    def save_review(self, review: ProviderReview) -> ProviderReview:
        raise NotImplementedError

    def list_reviews(self, provider_id: Optional[str] = None) -> List[ProviderReview]:
        raise NotImplementedError

    def save_referral(self, referral: ReferralRecord) -> ReferralRecord:
        raise NotImplementedError

    def list_referrals(self) -> List[ReferralRecord]:
        raise NotImplementedError

    def save_notification(self, notif: Notification) -> Notification:
        raise NotImplementedError

    def list_notifications(self, recipient: Optional[str] = None) -> List[Notification]:
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class InMemoryMedVoyageStorage(MedVoyageStorage):
    """Thread-safe in-memory storage backend."""

    def __init__(self):
        self._lock = RLock()
        self._inquiries: Dict[str, PatientInquiry] = {}
        self._bookings: Dict[str, ConsultationBooking] = {}
        self._aftercare: Dict[str, List[AftercareMilestone]] = {}
        self._treatments: Dict[str, Treatment] = {}
        self._providers: Dict[str, Provider] = {}
        self._cases: Dict[str, PatientCase] = {}
        self._reviews: Dict[str, ProviderReview] = {}
        self._referrals: Dict[str, ReferralRecord] = {}
        self._notifications: Dict[str, Notification] = {}

    def save_case(self, case: PatientCase) -> PatientCase:
        with self._lock:
            self._cases[case.id] = case
            return case

    def get_case(self, case_id: str) -> Optional[PatientCase]:
        with self._lock:
            return self._cases.get(case_id)

    def list_cases(self) -> List[PatientCase]:
        with self._lock:
            return list(self._cases.values())

    def update_case_status(self, case_id: str, status: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return False
            case.status = status
            if notes:
                case.clinical_notes = notes
            return True

    def save_review(self, review: ProviderReview) -> ProviderReview:
        with self._lock:
            self._reviews[review.id] = review
            return review

    def list_reviews(self, provider_id: Optional[str] = None) -> List[ProviderReview]:
        with self._lock:
            items = list(self._reviews.values())
            if provider_id:
                items = [r for r in items if r.provider_id == provider_id]
            return items

    def save_referral(self, referral: ReferralRecord) -> ReferralRecord:
        with self._lock:
            self._referrals[referral.id] = referral
            return referral

    def list_referrals(self) -> List[ReferralRecord]:
        with self._lock:
            return list(self._referrals.values())

    def save_notification(self, notif: Notification) -> Notification:
        with self._lock:
            self._notifications[notif.id] = notif
            return notif

    def list_notifications(self, recipient: Optional[str] = None) -> List[Notification]:
        with self._lock:
            items = list(self._notifications.values())
            if recipient:
                items = [n for n in items if n.recipient == recipient]
            return items

    def save_treatment(self, treatment: Treatment) -> Treatment:
        with self._lock:
            self._treatments[treatment.id] = treatment
            return treatment

    def list_treatments(self) -> List[Treatment]:
        with self._lock:
            return list(self._treatments.values())

    def save_provider(self, provider: Provider) -> Provider:
        with self._lock:
            self._providers[provider.id] = provider
            return provider

    def list_providers(self) -> List[Provider]:
        with self._lock:
            return list(self._providers.values())

    def save_inquiry(self, inquiry: PatientInquiry) -> PatientInquiry:
        with self._lock:
            self._inquiries[inquiry.id] = inquiry
            return inquiry

    def get_inquiry(self, inquiry_id: str) -> Optional[PatientInquiry]:
        with self._lock:
            return self._inquiries.get(inquiry_id)

    def list_inquiries(self) -> List[PatientInquiry]:
        with self._lock:
            return list(self._inquiries.values())

    def save_booking(self, booking: ConsultationBooking) -> ConsultationBooking:
        with self._lock:
            self._bookings[booking.booking_id] = booking
            return booking

    def get_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        with self._lock:
            return self._bookings.get(booking_id)

    def list_bookings(self) -> List[ConsultationBooking]:
        with self._lock:
            return list(self._bookings.values())

    def save_aftercare_milestones(
        self, booking_id: str, milestones: List[AftercareMilestone]
    ) -> List[AftercareMilestone]:
        with self._lock:
            self._aftercare[booking_id] = list(milestones)
            return milestones

    def get_aftercare_milestones(self, booking_id: str) -> List[AftercareMilestone]:
        with self._lock:
            return list(self._aftercare.get(booking_id, []))

    def complete_aftercare_milestone(self, booking_id: str, milestone_id: str) -> bool:
        with self._lock:
            items = self._aftercare.get(booking_id, [])
            for m in items:
                if m.id == milestone_id:
                    m.is_completed = True
                    return True
            return False

    def clear(self):
        with self._lock:
            self._inquiries.clear()
            self._bookings.clear()
            self._aftercare.clear()
            self._cases.clear()
            self._reviews.clear()
            self._referrals.clear()
            self._notifications.clear()


class SQLiteMedVoyageStorage(MedVoyageStorage):
    """Thread-safe persistent SQLite storage backend for MedVoyage."""

    def __init__(self, db_path: Union[str, Path] = "medvoyage.db"):
        self.db_path = str(db_path)
        self._lock = RLock()
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._lock:
            with self._connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS inquiries (
                        id TEXT PRIMARY KEY,
                        patient_name TEXT NOT NULL,
                        treatment_id TEXT NOT NULL,
                        budget_usd REAL NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bookings (
                        booking_id TEXT PRIMARY KEY,
                        inquiry_id TEXT NOT NULL,
                        provider_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        data TEXT NOT NULL,
                        scheduled_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS aftercare_milestones (
                        id TEXT PRIMARY KEY,
                        booking_id TEXT NOT NULL,
                        day_post_op INTEGER NOT NULL,
                        is_completed INTEGER NOT NULL,
                        data TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS treatments (
                        id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        data TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS providers (
                        id TEXT PRIMARY KEY,
                        specialty TEXT NOT NULL,
                        country TEXT NOT NULL,
                        data TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS patient_cases (
                        id TEXT PRIMARY KEY,
                        inquiry_id TEXT NOT NULL,
                        patient_name TEXT NOT NULL,
                        treatment_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reviews (
                        id TEXT PRIMARY KEY,
                        provider_id TEXT NOT NULL,
                        rating REAL NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS referrals (
                        id TEXT PRIMARY KEY,
                        referrer_email TEXT NOT NULL,
                        status TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        recipient TEXT NOT NULL,
                        category TEXT NOT NULL,
                        is_read INTEGER NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

    def save_treatment(self, treatment: Treatment) -> Treatment:
        with self._lock:
            data_json = treatment.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO treatments (id, category, name, data)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        category = excluded.category,
                        name = excluded.name,
                        data = excluded.data
                    """,
                    (treatment.id, treatment.category, treatment.name, data_json),
                )
            return treatment

    def list_treatments(self) -> List[Treatment]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM treatments ORDER BY name ASC")
                rows = cursor.fetchall()
                return [Treatment.model_validate_json(r["data"]) for r in rows]

    def save_provider(self, provider: Provider) -> Provider:
        with self._lock:
            data_json = provider.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO providers (id, specialty, country, data)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        specialty = excluded.specialty,
                        country = excluded.country,
                        data = excluded.data
                    """,
                    (provider.id, provider.specialty, provider.country, data_json),
                )
            return provider

    def list_providers(self) -> List[Provider]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM providers ORDER BY rating DESC")
                rows = cursor.fetchall()
                return [Provider.model_validate_json(r["data"]) for r in rows]

    def save_inquiry(self, inquiry: PatientInquiry) -> PatientInquiry:
        with self._lock:
            data_json = inquiry.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO inquiries (id, patient_name, treatment_id, budget_usd, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        patient_name = excluded.patient_name,
                        treatment_id = excluded.treatment_id,
                        budget_usd = excluded.budget_usd,
                        data = excluded.data
                    """,
                    (
                        inquiry.id,
                        inquiry.patient_name,
                        inquiry.treatment_id,
                        inquiry.budget_usd,
                        data_json,
                        inquiry.created_at.isoformat(),
                    ),
                )
            return inquiry

    def get_inquiry(self, inquiry_id: str) -> Optional[PatientInquiry]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM inquiries WHERE id = ?", (inquiry_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return PatientInquiry.model_validate_json(row["data"])

    def list_inquiries(self) -> List[PatientInquiry]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM inquiries ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [PatientInquiry.model_validate_json(r["data"]) for r in rows]

    def save_booking(self, booking: ConsultationBooking) -> ConsultationBooking:
        with self._lock:
            data_json = booking.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO bookings (booking_id, inquiry_id, provider_id, status, data, scheduled_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(booking_id) DO UPDATE SET
                        inquiry_id = excluded.inquiry_id,
                        provider_id = excluded.provider_id,
                        status = excluded.status,
                        data = excluded.data,
                        scheduled_at = excluded.scheduled_at
                    """,
                    (
                        booking.booking_id,
                        booking.inquiry_id,
                        booking.provider_id,
                        booking.status,
                        data_json,
                        booking.scheduled_at.isoformat(),
                    ),
                )
            return booking

    def get_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM bookings WHERE booking_id = ?", (booking_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return ConsultationBooking.model_validate_json(row["data"])

    def list_bookings(self) -> List[ConsultationBooking]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM bookings ORDER BY scheduled_at ASC")
                rows = cursor.fetchall()
                return [ConsultationBooking.model_validate_json(r["data"]) for r in rows]

    def save_aftercare_milestones(
        self, booking_id: str, milestones: List[AftercareMilestone]
    ) -> List[AftercareMilestone]:
        with self._lock:
            with self._connection() as conn:
                for m in milestones:
                    data_json = m.model_dump_json()
                    conn.execute(
                        """
                        INSERT INTO aftercare_milestones (id, booking_id, day_post_op, is_completed, data)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            is_completed = excluded.is_completed,
                            data = excluded.data
                        """,
                        (m.id, booking_id, m.day_post_op, 1 if m.is_completed else 0, data_json),
                    )
            return milestones

    def get_aftercare_milestones(self, booking_id: str) -> List[AftercareMilestone]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM aftercare_milestones WHERE booking_id = ? ORDER BY day_post_op ASC",
                    (booking_id,),
                )
                rows = cursor.fetchall()
                return [AftercareMilestone.model_validate_json(r["data"]) for r in rows]

    def complete_aftercare_milestone(self, booking_id: str, milestone_id: str) -> bool:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM aftercare_milestones WHERE booking_id = ? AND id = ?",
                    (booking_id, milestone_id),
                )
                row = cursor.fetchone()
                if not row:
                    return False
                m = AftercareMilestone.model_validate_json(row["data"])
                m.is_completed = True
                conn.execute(
                    "UPDATE aftercare_milestones SET is_completed = 1, data = ? WHERE id = ?",
                    (m.model_dump_json(), milestone_id),
                )
                return True

    def save_case(self, case: PatientCase) -> PatientCase:
        with self._lock:
            data_json = case.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO patient_cases (id, inquiry_id, patient_name, treatment_id, status, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        data = excluded.data
                    """,
                    (case.id, case.inquiry_id, case.patient_name, case.treatment_id, str(case.status), data_json, case.created_at.isoformat()),
                )
            return case

    def get_case(self, case_id: str) -> Optional[PatientCase]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM patient_cases WHERE id = ?", (case_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return PatientCase.model_validate_json(row["data"])

    def list_cases(self) -> List[PatientCase]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM patient_cases ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [PatientCase.model_validate_json(r["data"]) for r in rows]

    def update_case_status(self, case_id: str, status: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            case = self.get_case(case_id)
            if not case:
                return False
            case.status = status
            if notes:
                case.clinical_notes = notes
            self.save_case(case)
            return True

    def save_review(self, review: ProviderReview) -> ProviderReview:
        with self._lock:
            data_json = review.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO reviews (id, provider_id, rating, data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        rating = excluded.rating,
                        data = excluded.data
                    """,
                    (review.id, review.provider_id, review.rating, data_json, review.created_at.isoformat()),
                )
            return review

    def list_reviews(self, provider_id: Optional[str] = None) -> List[ProviderReview]:
        with self._lock:
            with self._connection() as conn:
                if provider_id:
                    cursor = conn.execute("SELECT data FROM reviews WHERE provider_id = ? ORDER BY created_at DESC", (provider_id,))
                else:
                    cursor = conn.execute("SELECT data FROM reviews ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [ProviderReview.model_validate_json(r["data"]) for r in rows]

    def save_referral(self, referral: ReferralRecord) -> ReferralRecord:
        with self._lock:
            data_json = referral.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO referrals (id, referrer_email, status, data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        data = excluded.data
                    """,
                    (referral.id, referral.referrer_email, referral.status, data_json, referral.created_at.isoformat()),
                )
            return referral

    def list_referrals(self) -> List[ReferralRecord]:
        with self._lock:
            with self._connection() as conn:
                cursor = conn.execute("SELECT data FROM referrals ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [ReferralRecord.model_validate_json(r["data"]) for r in rows]

    def save_notification(self, notif: Notification) -> Notification:
        with self._lock:
            data_json = notif.model_dump_json()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO notifications (id, recipient, category, is_read, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        is_read = excluded.is_read,
                        data = excluded.data
                    """,
                    (notif.id, notif.recipient, notif.category, 1 if notif.is_read else 0, data_json, notif.created_at.isoformat()),
                )
            return notif

    def list_notifications(self, recipient: Optional[str] = None) -> List[Notification]:
        with self._lock:
            with self._connection() as conn:
                if recipient:
                    cursor = conn.execute("SELECT data FROM notifications WHERE recipient = ? ORDER BY created_at DESC", (recipient,))
                else:
                    cursor = conn.execute("SELECT data FROM notifications ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [Notification.model_validate_json(r["data"]) for r in rows]

    def clear(self):
        with self._lock:
            with self._connection() as conn:
                conn.execute("DELETE FROM inquiries")
                conn.execute("DELETE FROM bookings")
                conn.execute("DELETE FROM aftercare_milestones")
                conn.execute("DELETE FROM treatments")
                conn.execute("DELETE FROM providers")
                conn.execute("DELETE FROM patient_cases")
                conn.execute("DELETE FROM reviews")
                conn.execute("DELETE FROM referrals")
                conn.execute("DELETE FROM notifications")
