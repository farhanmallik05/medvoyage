"""Data models for MedVoyage medical tourism marketplace."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Urgency(str, Enum):
    FLEXIBLE = "FLEXIBLE"
    WITHIN_MONTH = "WITHIN_MONTH"
    URGENT = "URGENT"


class Destination(BaseModel):
    id: str
    country: str
    city: str
    description: str
    visa_policy: str
    international_hub: str
    average_hotel_cost_usd_per_night: float
    jci_hospitals_count: int


class Treatment(BaseModel):
    id: str
    category: str  # Orthopedics, Cardiology, Oncology, Dental, Cosmetic, Ophthalmology
    name: str
    description: str
    typical_stay_days: int
    recovery_days: int
    us_benchmark_cost_usd: float


class Hospital(BaseModel):
    id: str
    name: str
    country: str
    city: str
    jci_accredited: bool = True
    established_year: int
    bed_count: int
    international_patient_concierge: bool = True
    airport_transfer_included: bool = True
    translators_available: List[str] = Field(default_factory=list)


class Provider(BaseModel):
    id: str
    name: str
    title: str
    specialty: str
    hospital_id: str
    hospital_name: str
    country: str
    city: str
    years_experience: int
    credentials: List[str]
    languages: List[str]
    rating: float
    verified: bool = True
    successful_cases: int


class PatientInquiry(BaseModel):
    id: str = Field(default_factory=lambda: f"inq-{uuid.uuid4().hex[:8]}")
    patient_name: str
    patient_email: str
    patient_country: str
    treatment_id: str
    budget_usd: float
    preferred_destinations: List[str] = Field(default_factory=list)
    urgency: Urgency = Urgency.WITHIN_MONTH
    preferred_language: str = "en"
    medical_records_summary: str
    created_at: datetime = Field(default_factory=utc_now)


class MatchScore(BaseModel):
    provider_id: str
    provider_name: str
    hospital_name: str
    country: str
    total_score: float  # 0.0 to 100.0
    clinical_score: float
    budget_score: float
    logistics_score: float
    rationale: str
    estimated_quote_usd: float


class ItemizedQuote(BaseModel):
    quote_id: str = Field(default_factory=lambda: f"qt-{uuid.uuid4().hex[:8]}")
    inquiry_id: Optional[str] = None
    provider_id: str
    provider_name: str
    hospital_id: str
    hospital_name: str
    treatment_name: str
    country: str
    base_procedure_usd: float
    surgeon_fee_usd: float
    facility_stay_usd: float
    anesthesia_meds_usd: float
    total_package_usd: float
    included_services: List[str]
    disclosed_additional_expenses: List[str]
    consultation_availability: str
    estimated_waiting_days: int
    aftercare_arrangements: str
    provider_qualifications_summary: str


class ConsultationBooking(BaseModel):
    booking_id: str = Field(default_factory=lambda: f"bk-{uuid.uuid4().hex[:8]}")
    inquiry_id: str
    provider_id: str
    scheduled_at: datetime
    consultation_type: str = "telehealth_video"
    status: str = "CONFIRMED"
    meeting_url: str = "https://telehealth.medvoyage.io/room/demo"
    notes: Optional[str] = None


class AftercareMilestone(BaseModel):
    id: str = Field(default_factory=lambda: f"aft-{uuid.uuid4().hex[:8]}")
    booking_id: str
    day_post_op: int
    title: str
    instructions: str
    is_completed: bool = False
    telehealth_checkin_required: bool = False


class LeadStatus(str, Enum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    MEDICAL_REVIEW = "MEDICAL_REVIEW"
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    QUOTE_SENT = "QUOTE_SENT"
    CONSULTATION = "CONSULTATION"
    BOOKED = "BOOKED"
    TREATMENT = "TREATMENT"
    AFTERCARE = "AFTERCARE"
    CLOSED = "CLOSED"


class PatientCase(BaseModel):
    id: str = Field(default_factory=lambda: f"case-{uuid.uuid4().hex[:8]}")
    inquiry_id: str
    patient_name: str
    patient_email: str
    treatment_id: str
    status: LeadStatus = LeadStatus.NEW
    assigned_provider_id: Optional[str] = None
    uploaded_files: List[str] = Field(default_factory=list)
    clinical_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProviderReview(BaseModel):
    id: str = Field(default_factory=lambda: f"rev-{uuid.uuid4().hex[:8]}")
    provider_id: str
    patient_name: str
    patient_country: str
    treatment_name: str
    rating: float  # 1.0 to 5.0
    comment: str
    verified_patient: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class ReferralRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"ref-{uuid.uuid4().hex[:8]}")
    referrer_name: str
    referrer_type: str  # Clinic, Doctor, Nurse, Medical Partner
    referrer_email: str
    patient_name: str
    booking_id: Optional[str] = None
    billed_amount_usd: float = 0.0
    commission_pct: float = 5.0  # 5% commission per EthAum PRD
    commission_earned_usd: float = 0.0
    status: str = "PENDING"  # PENDING, APPROVED, PAID
    created_at: datetime = Field(default_factory=utc_now)


class Notification(BaseModel):
    id: str = Field(default_factory=lambda: f"notif-{uuid.uuid4().hex[:8]}")
    recipient: str  # e.g., "patient", "provider", or user email
    title: str
    message: str
    category: str = "general"  # inquiry, quote, booking, aftercare
    is_read: bool = False
    created_at: datetime = Field(default_factory=utc_now)
