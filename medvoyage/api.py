"""REST API and Web Marketplace Interface for MedVoyage.
EthAum Venture Partners Track: Building Medical Tourism Platform.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from medvoyage.aftercare import AFTERCARE_MANAGER
from medvoyage.booking import BOOKING_MANAGER
from medvoyage.catalog import DESTINATIONS, HOSPITALS, PROVIDERS, TREATMENTS, get_provider_by_id, get_treatment_by_id
from medvoyage.matcher import match_providers_for_inquiry
from medvoyage.models import ConsultationBooking, ItemizedQuote, MatchScore, PatientInquiry, Urgency
from medvoyage.quote_engine import compare_quotes_for_treatment
from medvoyage.sample_data import seed_sample_marketplace_data

app = FastAPI(
    title="MedVoyage Marketplace API",
    description="Transparent Medical Tourism Platform with AI Provider Matching & Itemized Quote Comparison.",
    version="0.1.0",
)

INQUIRIES: List[PatientInquiry] = seed_sample_marketplace_data()


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


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "MedVoyage Marketplace",
        "track": "EthAum Venture Partners Medical Tourism",
    }


@app.get("/api/destinations")
def list_destinations():
    return DESTINATIONS


@app.get("/api/treatments")
def list_treatments():
    return TREATMENTS


@app.get("/api/providers")
def list_providers(specialty: Optional[str] = None, country: Optional[str] = None):
    results = PROVIDERS
    if specialty:
        results = [p for p in results if p.specialty.lower() == specialty.lower()]
    if country:
        results = [p for p in results if p.country.lower() == country.lower()]
    return results


@app.get("/api/hospitals")
def list_hospitals():
    return HOSPITALS


@app.post("/api/inquiries", response_model=PatientInquiry)
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
    INQUIRIES.append(inq)
    return inq


@app.post("/api/match", response_model=List[MatchScore])
def match_providers(inquiry: PatientInquiry):
    return match_providers_for_inquiry(inquiry)


@app.get("/api/quotes/compare", response_model=List[ItemizedQuote])
def compare_quotes(treatment_id: str = Query(..., description="ID of the treatment to compare")):
    try:
        return compare_quotes_for_treatment(treatment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/bookings", response_model=ConsultationBooking)
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


@app.post("/api/aftercare/{booking_id}/complete/{milestone_id}")
def complete_aftercare_milestone(booking_id: str, milestone_id: str):
    ok = AFTERCARE_MANAGER.complete_milestone(booking_id, milestone_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {"status": "success", "milestone_id": milestone_id, "completed": True}


@app.get("/", response_class=HTMLResponse)
def marketplace_homepage():
    # Build comparison cards for knee replacement
    quotes = compare_quotes_for_treatment("knee-replacement")
    quote_cards = "".join(
        f"""
        <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 flex flex-col justify-between hover:border-emerald-500 transition">
            <div>
                <div class="flex justify-between items-start">
                    <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">{q.country}</span>
                    <span class="text-xs text-gray-500 font-medium">Wait: {q.estimated_waiting_days} days</span>
                </div>
                <h3 class="text-lg font-bold text-gray-900 mt-3">{q.provider_name}</h3>
                <p class="text-xs text-gray-500">{q.hospital_name}</p>
                <div class="mt-4 pb-4 border-b border-gray-100">
                    <div class="text-xs text-gray-400">Total Transparent Package</div>
                    <div class="text-3xl font-extrabold text-gray-900">${q.total_package_usd:,.0f} <span class="text-xs text-gray-400 font-normal">USD</span></div>
                    <div class="text-xs text-emerald-600 font-medium mt-1">Saves ~{round((38000 - q.total_package_usd)/38000*100)}% vs US Benchmark ($38,000)</div>
                </div>
                <div class="mt-4 space-y-2">
                    <div class="text-xs font-semibold text-gray-700">Itemized Cost Breakdown:</div>
                    <div class="flex justify-between text-xs text-gray-600"><span>Procedure & OR:</span><span>${q.base_procedure_usd:,.0f}</span></div>
                    <div class="flex justify-between text-xs text-gray-600"><span>Surgeon & Anesthesia:</span><span>${q.surgeon_fee_usd + q.anesthesia_meds_usd:,.0f}</span></div>
                    <div class="flex justify-between text-xs text-gray-600"><span>Private Suite Hospital Stay:</span><span>${q.facility_stay_usd:,.0f}</span></div>
                </div>
                <div class="mt-4">
                    <div class="text-xs font-semibold text-emerald-800">Included Services (Guaranteed):</div>
                    <ul class="text-xs text-gray-600 mt-1 list-disc pl-4 space-y-1">
                        {"".join(f"<li>{s}</li>" for s in q.included_services[:3])}
                    </ul>
                </div>
                <div class="mt-4 bg-amber-50/60 p-3 rounded-lg border border-amber-100">
                    <div class="text-xs font-semibold text-amber-800">Disclosed Additional Expenses:</div>
                    <ul class="text-xs text-amber-900 mt-1 list-disc pl-4 space-y-0.5">
                        {"".join(f"<li>{s}</li>" for s in q.disclosed_additional_expenses[:2])}
                    </ul>
                </div>
            </div>
            <div class="mt-6 pt-4 border-t border-gray-100">
                <div class="text-xs text-gray-500 mb-3"><span class="font-semibold text-gray-700">Aftercare:</span> {q.aftercare_arrangements}</div>
                <button class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm py-2.5 rounded-xl transition shadow-sm">
                    Book Telehealth Consultation &rarr;
                </button>
            </div>
        </div>
        """
        for q in quotes
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>MedVoyage | Transparent Medical Tourism Platform</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 text-gray-900 font-sans antialiased">
        <!-- Navigation -->
        <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl font-black text-emerald-600 tracking-tight">MedVoyage</span>
                    <span class="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono">EthAum MVP</span>
                </div>
                <div class="flex items-center space-x-6 text-sm font-medium text-gray-600">
                    <a href="#compare" class="hover:text-emerald-600">Transparent Comparison</a>
                    <a href="#destinations" class="hover:text-emerald-600">Destinations</a>
                    <a href="/docs" class="text-emerald-600 font-semibold hover:underline">API & Swagger &rarr;</a>
                </div>
            </div>
        </nav>

        <!-- Hero Header -->
        <header class="bg-gradient-to-b from-emerald-50/50 to-transparent py-14 px-6 border-b border-gray-100">
            <div class="max-w-4xl mx-auto text-center">
                <div class="inline-block bg-emerald-100 text-emerald-800 text-xs px-3 py-1 rounded-full font-semibold uppercase tracking-wider mb-4">
                    Zero Hidden Costs &bull; JCI-Accredited Hospitals &bull; Verified Specialists
                </div>
                <h1 class="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
                    Transparent Medical Tourism Comparison
                </h1>
                <p class="text-lg text-slate-600 mt-4 leading-relaxed">
                    Compare true itemized procedure packages, JCI-accredited surgeon credentials, and comprehensive aftercare arrangements across international hubs.
                </p>
            </div>
        </header>

        <!-- Main Marketplace Comparison Section -->
        <main class="max-w-7xl mx-auto px-6 py-12 space-y-12">
            <section id="compare">
                <div class="flex justify-between items-end mb-8">
                    <div>
                        <h2 class="text-2xl font-bold text-slate-900">Featured Comparison: Total Knee Replacement</h2>
                        <p class="text-sm text-slate-500 mt-1">Comparing verified JCI hospital quotes side-by-side with anti-surprise billing transparency.</p>
                    </div>
                    <span class="text-xs text-gray-400">US Benchmark: $38,000 USD</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {quote_cards}
                </div>
            </section>

            <!-- EthAum Differentiator Banner -->
            <section class="bg-slate-900 text-white rounded-3xl p-8 md:p-12 shadow-xl">
                <div class="max-w-3xl">
                    <h2 class="text-2xl font-bold">Why MedVoyage Wins Over Legacy Directories</h2>
                    <p class="text-slate-300 text-sm mt-3 leading-relaxed">
                        Legacy medical travel sites operate as opaque lead generation boards with hidden facility surcharges and abandoned post-op care. MedVoyage guarantees end-to-end transparency: itemized price disclosures, AI-driven provider matching, and structured 90-day recovery telehealth tracking.
                    </p>
                    <div class="grid grid-cols-3 gap-6 mt-8 pt-8 border-t border-slate-800 text-center">
                        <div>
                            <div class="text-3xl font-extrabold text-emerald-400">100%</div>
                            <div class="text-xs text-slate-400 mt-1">Disclosed Extra Costs</div>
                        </div>
                        <div>
                            <div class="text-3xl font-extrabold text-emerald-400">JCI Only</div>
                            <div class="text-xs text-slate-400 mt-1">Accredited Centers</div>
                        </div>
                        <div>
                            <div class="text-3xl font-extrabold text-emerald-400">90-Day</div>
                            <div class="text-xs text-slate-400 mt-1">Continuous Aftercare</div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
