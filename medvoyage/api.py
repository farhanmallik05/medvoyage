"""REST API and Web Marketplace Interface for MedVoyage.
EthAum Venture Partners Track: Building Medical Tourism Platform.
Includes SQLite persistence, API key authentication, clinical NLP record extractor, and catalog ingestion.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, Security
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from medvoyage.aftercare import AFTERCARE_MANAGER
from medvoyage.booking import BOOKING_MANAGER
from medvoyage.catalog import DESTINATIONS, HOSPITALS, PROVIDERS, TREATMENTS, get_destination_by_id, get_hospital_by_id, get_provider_by_id, get_treatment_by_id
import medvoyage.catalog as cat
from medvoyage.extractor import ExtractedClinicalInquiry, extract_clinical_inquiry
from medvoyage.ingestion import (
    IngestionError,
    ingest_providers_csv,
    ingest_providers_json,
    ingest_treatments_csv,
    ingest_treatments_json,
)
from medvoyage.matcher import match_providers_for_inquiry
from medvoyage.models import ConsultationBooking, ItemizedQuote, MatchScore, PatientInquiry, Urgency
from medvoyage.quote_engine import compare_quotes_for_treatment
from medvoyage.sample_data import (
    seed_sample_marketplace_data,
    seed_sample_notifications,
    seed_sample_referrals,
    seed_sample_reviews,
)
from medvoyage.storage import InMemoryMedVoyageStorage, SQLiteMedVoyageStorage

app = FastAPI(
    title="MedVoyage Marketplace API",
    description="Transparent Medical Tourism Platform with AI Provider Matching & Itemized Quote Comparison.",
    version="0.2.0",
)

# Setup Templates & Static Paths
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# API Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    expected = os.environ.get("MEDVOYAGE_API_KEY")
    if expected:
        if not api_key or api_key != expected:
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
    return api_key


# Storage Backend
db_path = os.environ.get("MEDVOYAGE_DB_PATH")
storage = SQLiteMedVoyageStorage(db_path) if db_path else InMemoryMedVoyageStorage()
BOOKING_MANAGER.set_storage(storage)
AFTERCARE_MANAGER.set_storage(storage)

# Sync treatments & providers with storage
stored_treatments = storage.list_treatments()
if stored_treatments:
    for st in stored_treatments:
        idx = next((i for i, t in enumerate(cat.TREATMENTS) if t.id == st.id), None)
        if idx is not None:
            cat.TREATMENTS[idx] = st
        else:
            cat.TREATMENTS.append(st)
else:
    for t in cat.TREATMENTS:
        storage.save_treatment(t)

stored_providers = storage.list_providers()
if stored_providers:
    for sp in stored_providers:
        idx = next((i for i, p in enumerate(cat.PROVIDERS) if p.id == sp.id), None)
        if idx is not None:
            cat.PROVIDERS[idx] = sp
        else:
            cat.PROVIDERS.append(sp)
else:
    for p in cat.PROVIDERS:
        storage.save_provider(p)

# Seed inquiries, reviews, referrals, and notifications if storage is brand new
if not storage.list_inquiries():
    for inq in seed_sample_marketplace_data():
        storage.save_inquiry(inq)
if not storage.list_reviews():
    for rev in seed_sample_reviews():
        storage.save_review(rev)
if not storage.list_referrals():
    for ref in seed_sample_referrals():
        storage.save_referral(ref)
if not storage.list_notifications():
    for notif in seed_sample_notifications():
        storage.save_notification(notif)


class CreateInquiryRequest(BaseModel):
    patient_name: str
    patient_email: str
    patient_country: str
    treatment_id: str
    budget_usd: float
    preferred_destinations: List[str] = []
    urgency: Urgency = Urgency.WITHIN_MONTH
    preferred_language: str = "en"
    medical_records_summary: str


class CreateBookingRequest(BaseModel):
    inquiry_id: str
    provider_id: str
    scheduled_at: datetime
    consultation_type: str = "telehealth_video"
    notes: Optional[str] = None


class ExtractRecordsRequest(BaseModel):
    medical_records_text: str


class CatalogIngestRequest(BaseModel):
    entity_type: str  # "treatment" or "provider"
    format: str  # "json" or "csv"
    content: str


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "MedVoyage Marketplace",
        "track": "EthAum Venture Partners Medical Tourism",
        "storage": "SQLite" if isinstance(storage, SQLiteMedVoyageStorage) else "In-Memory",
        "auth_enabled": bool(os.environ.get("MEDVOYAGE_API_KEY")),
        "nlp_extractor_ready": True,
        "catalog_ingestion_ready": True,
    }


@app.get("/api/destinations")
def list_destinations():
    return DESTINATIONS


@app.get("/api/treatments")
def list_treatments():
    return cat.TREATMENTS


@app.get("/api/providers")
def list_providers(specialty: Optional[str] = None, country: Optional[str] = None):
    results = cat.PROVIDERS
    if specialty:
        results = [p for p in results if p.specialty.lower() == specialty.lower()]
    if country:
        results = [p for p in results if p.country.lower() == country.lower()]
    return results


@app.get("/api/hospitals")
def list_hospitals():
    return HOSPITALS


@app.get("/api/inquiries", response_model=List[PatientInquiry])
def list_inquiries():
    return storage.list_inquiries()


@app.post("/api/inquiries", response_model=PatientInquiry, dependencies=[Depends(verify_api_key)])
def submit_inquiry(req: CreateInquiryRequest):
    treatment = get_treatment_by_id(req.treatment_id)
    if not treatment:
        raise HTTPException(status_code=400, detail=f"Treatment '{req.treatment_id}' not found")

    inq = PatientInquiry(
        patient_name=req.patient_name,
        patient_email=req.patient_email,
        patient_country=req.patient_country,
        treatment_id=req.treatment_id,
        budget_usd=req.budget_usd,
        preferred_destinations=req.preferred_destinations,
        urgency=req.urgency,
        preferred_language=req.preferred_language,
        medical_records_summary=req.medical_records_summary,
    )
    storage.save_inquiry(inq)
    return inq


@app.post("/api/inquiries/extract-records", response_model=ExtractedClinicalInquiry)
def extract_records(req: ExtractRecordsRequest):
    """Parses messy, unstructured medical records or clinical notes into structured inquiry parameters."""
    if not req.medical_records_text or len(req.medical_records_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Medical records text must be at least 10 characters long")
    return extract_clinical_inquiry(req.medical_records_text)


@app.post("/api/catalog/ingest", dependencies=[Depends(verify_api_key)])
def ingest_catalog_data(req: CatalogIngestRequest):
    """Schema-based ingestion pipeline for treatments and providers via CSV or JSON."""
    entity = req.entity_type.lower()
    fmt = req.format.lower()

    try:
        if entity == "treatment":
            if fmt == "json":
                items, errors = ingest_treatments_json(req.content, storage=storage)
            elif fmt == "csv":
                items, errors = ingest_treatments_csv(req.content, storage=storage)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format '{req.format}'. Use 'json' or 'csv'")
        elif entity == "provider":
            if fmt == "json":
                items, errors = ingest_providers_json(req.content, storage=storage)
            elif fmt == "csv":
                items, errors = ingest_providers_csv(req.content, storage=storage)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format '{req.format}'. Use 'json' or 'csv'")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported entity_type '{req.entity_type}'. Use 'treatment' or 'provider'")

        return {
            "status": "success",
            "entity_type": entity,
            "format": fmt,
            "ingested_count": len(items),
            "errors": errors,
        }
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail=str(ie))


@app.post("/api/match", response_model=List[MatchScore])
def match_providers(inquiry: PatientInquiry):
    return match_providers_for_inquiry(inquiry)


@app.get("/api/quotes/compare", response_model=List[ItemizedQuote])
def compare_quotes(treatment_id: str = Query(..., description="ID of the treatment to compare")):
    try:
        return compare_quotes_for_treatment(treatment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/bookings", response_model=ConsultationBooking, dependencies=[Depends(verify_api_key)])
def create_booking(req: CreateBookingRequest):
    try:
        booking = BOOKING_MANAGER.create_booking(
            inquiry_id=req.inquiry_id,
            provider_id=req.provider_id,
            scheduled_at=req.scheduled_at,
            consultation_type=req.consultation_type,
            notes=req.notes,
        )
        provider = get_provider_by_id(req.provider_id)
        AFTERCARE_MANAGER.generate_plan(
            booking.booking_id,
            treatment_category=provider.specialty if provider else "General",
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/bookings")
def list_bookings():
    return BOOKING_MANAGER.list_bookings()


@app.get("/api/aftercare/{booking_id}")
def get_aftercare(booking_id: str):
    plan = AFTERCARE_MANAGER.get_plan(booking_id)
    return {"booking_id": booking_id, "milestones": plan}


@app.post("/api/aftercare/{booking_id}/complete/{milestone_id}", dependencies=[Depends(verify_api_key)])
def complete_aftercare_milestone(booking_id: str, milestone_id: str):
    ok = AFTERCARE_MANAGER.complete_milestone(booking_id, milestone_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {"status": "success", "milestone_id": milestone_id, "completed": True}


# ============================================================================
# Web Marketplace UI Routes (PRD Full Patient & Provider Journeys)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def marketplace_homepage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "treatments": cat.TREATMENTS,
            "destinations": DESTINATIONS,
            "providers": cat.PROVIDERS,
        },
    )


@app.get("/treatments", response_class=HTMLResponse)
def treatments_catalog_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="treatments.html",
        context={"treatments": cat.TREATMENTS},
    )


@app.get("/treatments/{treatment_id}", response_class=HTMLResponse)
def treatment_detail_page(request: Request, treatment_id: str):
    treatment = get_treatment_by_id(treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    return templates.TemplateResponse(
        request=request,
        name="treatment_detail.html",
        context={"treatment": treatment},
    )


@app.get("/destinations", response_class=HTMLResponse)
def destinations_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="destinations.html",
        context={"destinations": DESTINATIONS},
    )


@app.get("/destinations/{destination_id}", response_class=HTMLResponse)
def destination_detail_page(request: Request, destination_id: str):
    dest = get_destination_by_id(destination_id)
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    dest_hospitals = [h for h in HOSPITALS if h.country.lower() == dest.country.lower()]
    return templates.TemplateResponse(
        request=request,
        name="destination_detail.html",
        context={"destination": dest, "hospitals": dest_hospitals},
    )


@app.get("/providers", response_class=HTMLResponse)
def providers_page(
    request: Request,
    specialty: Optional[str] = None,
    country: Optional[str] = None,
):
    providers = cat.PROVIDERS
    if specialty:
        providers = [p for p in providers if p.specialty.lower() == specialty.lower()]
    if country:
        providers = [p for p in providers if p.country.lower() == country.lower()]
    return templates.TemplateResponse(
        request=request,
        name="providers.html",
        context={
            "providers": providers,
            "selected_specialty": specialty,
            "selected_country": country,
        },
    )


@app.get("/providers/{provider_id}", response_class=HTMLResponse)
def provider_detail_page(request: Request, provider_id: str):
    provider = get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    hospital = get_hospital_by_id(provider.hospital_id)
    reviews = storage.list_reviews(provider_id=provider_id)
    return templates.TemplateResponse(
        request=request,
        name="provider_detail.html",
        context={
            "provider": provider,
            "hospital": hospital,
            "reviews": reviews,
        },
    )


@app.get("/inquiry/new", response_class=HTMLResponse)
def new_inquiry_page(request: Request, treatment: Optional[str] = None):
    return templates.TemplateResponse(
        request=request,
        name="inquiry_form.html",
        context={
            "treatments": cat.TREATMENTS,
            "destinations": DESTINATIONS,
            "selected_treatment": treatment,
        },
    )


@app.post("/inquiry/new")
def submit_new_inquiry_form(
    patient_name: str = Form(...),
    patient_email: str = Form(...),
    patient_country: str = Form(...),
    treatment_id: str = Form(...),
    budget_usd: float = Form(...),
    preferred_destinations: List[str] = Form([]),
    urgency: Urgency = Form(Urgency.WITHIN_MONTH),
    preferred_language: str = Form("en"),
    medical_records_summary: str = Form(...),
):
    inq = PatientInquiry(
        patient_name=patient_name,
        patient_email=patient_email,
        patient_country=patient_country,
        treatment_id=treatment_id,
        budget_usd=budget_usd,
        preferred_destinations=preferred_destinations,
        urgency=urgency,
        preferred_language=preferred_language,
        medical_records_summary=medical_records_summary,
    )
    storage.save_inquiry(inq)
    return RedirectResponse(url=f"/inquiry/{inq.id}/matches", status_code=303)


@app.get("/inquiry/{inquiry_id}/matches", response_class=HTMLResponse)
def inquiry_matches_page(request: Request, inquiry_id: str):
    inquiry = storage.get_inquiry(inquiry_id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    matches = match_providers_for_inquiry(inquiry)
    return templates.TemplateResponse(
        request=request,
        name="matches.html",
        context={"inquiry": inquiry, "matches": matches},
    )


@app.get("/compare", response_class=HTMLResponse)
def compare_quotes_page(request: Request, treatment: Optional[str] = "knee-replacement"):
    treatment_id = treatment or "knee-replacement"
    quotes = compare_quotes_for_treatment(treatment_id)
    sel_t = get_treatment_by_id(treatment_id)
    benchmark = sel_t.us_benchmark_cost_usd if sel_t else 38000.0
    return templates.TemplateResponse(
        request=request,
        name="compare.html",
        context={
            "quotes": quotes,
            "all_treatments": cat.TREATMENTS,
            "selected_treatment": treatment_id,
            "benchmark_cost": benchmark,
        },
    )


@app.get("/book/{provider_id}", response_class=HTMLResponse)
def book_consultation_page(request: Request, provider_id: str, inquiry_id: Optional[str] = None):
    provider = get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return templates.TemplateResponse(
        request=request,
        name="book.html",
        context={"provider": provider, "inquiry_id": inquiry_id},
    )


@app.post("/book/{provider_id}")
def process_book_consultation_form(
    provider_id: str,
    inquiry_id: str = Form(...),
    scheduled_at: str = Form(...),
    consultation_type: str = Form("telehealth_video"),
    notes: Optional[str] = Form(None),
):
    try:
        sched_dt = datetime.fromisoformat(scheduled_at)
    except Exception:
        sched_dt = datetime.now(timezone.utc)

    booking = BOOKING_MANAGER.create_booking(
        inquiry_id=inquiry_id,
        provider_id=provider_id,
        scheduled_at=sched_dt,
        consultation_type=consultation_type,
        notes=notes,
    )
    provider = get_provider_by_id(provider_id)
    AFTERCARE_MANAGER.generate_plan(
        booking.booking_id,
        treatment_category=provider.specialty if provider else "General",
    )
    return RedirectResponse(url=f"/aftercare/{booking.booking_id}", status_code=303)


@app.get("/aftercare/{booking_id}", response_class=HTMLResponse)
def aftercare_page(request: Request, booking_id: str):
    milestones = AFTERCARE_MANAGER.get_plan(booking_id)
    return templates.TemplateResponse(
        request=request,
        name="aftercare.html",
        context={"booking_id": booking_id, "milestones": milestones},
    )


@app.get("/records/upload", response_class=HTMLResponse)
def records_upload_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={},
    )


@app.get("/referral", response_class=HTMLResponse)
def referral_program_page(request: Request):
    referrals = storage.list_referrals()
    return templates.TemplateResponse(
        request=request,
        name="referral.html",
        context={"referrals": referrals},
    )


@app.get("/help", response_class=HTMLResponse)
def help_centre_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="help.html",
        context={},
    )


# ============================================================================
# Hospital / Provider Portal Routes (PRD Section 3 CRM & Section 7 Analytics)
# ============================================================================

@app.get("/portal/leads", response_class=HTMLResponse)
def portal_leads_inbox(request: Request):
    inquiries = storage.list_inquiries()
    return templates.TemplateResponse(
        request=request,
        name="portal_leads.html",
        context={"inquiries": inquiries},
    )


@app.get("/portal/leads/{inquiry_id}", response_class=HTMLResponse)
def portal_lead_detail_page(request: Request, inquiry_id: str):
    inq = storage.get_inquiry(inquiry_id)
    if not inq:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return templates.TemplateResponse(
        request=request,
        name="portal_lead_detail.html",
        context={"inquiry": inq},
    )


@app.get("/portal/quote/new", response_class=HTMLResponse)
def portal_quote_builder_page(request: Request, inquiry_id: Optional[str] = None):
    return templates.TemplateResponse(
        request=request,
        name="portal_quote_builder.html",
        context={
            "inquiry_id": inquiry_id,
            "hospitals": HOSPITALS,
            "providers": cat.PROVIDERS,
        },
    )


@app.post("/portal/quote/send")
def portal_quote_send_action(inquiry_id: Optional[str] = Form(None)):
    return RedirectResponse(url="/portal/leads", status_code=303)


@app.get("/portal/appointments", response_class=HTMLResponse)
def portal_appointments_page(request: Request):
    bookings = storage.list_bookings()
    return templates.TemplateResponse(
        request=request,
        name="portal_appointments.html",
        context={"bookings": bookings},
    )


@app.get("/portal/analytics", response_class=HTMLResponse)
def portal_analytics_dashboard(request: Request):
    inquiries = storage.list_inquiries()
    bookings = storage.list_bookings()
    total_inquiries = len(inquiries)
    total_bookings = len(bookings)
    conv_rate = round((total_bookings / total_inquiries * 100), 1) if total_inquiries > 0 else 0.0
    pipeline_usd = sum(i.budget_usd for i in inquiries)

    return templates.TemplateResponse(
        request=request,
        name="portal_analytics.html",
        context={
            "total_inquiries": total_inquiries,
            "total_bookings": total_bookings,
            "conversion_rate": conv_rate,
            "total_pipeline_usd": pipeline_usd,
        },
    )
