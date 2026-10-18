"""Quote engine: Generates transparent, itemized treatment quotes with disclosed extras."""

from typing import Dict, List, Optional
from medvoyage.catalog import get_hospital_by_id, get_provider_by_id, get_treatment_by_id
from medvoyage.models import ItemizedQuote, PatientInquiry


# Transparent baseline cost multipliers by destination relative to US benchmark
DESTINATION_COST_RATIOS = {
    "India": 0.22,               # ~78% savings vs US
    "Thailand": 0.32,            # ~68% savings vs US
    "Turkey": 0.28,              # ~72% savings vs US
    "United Arab Emirates": 0.45,# ~55% savings vs US (premium world-class hub)
    "Singapore": 0.55,           # ~45% savings vs US
}


def build_transparent_quote(
    provider_id: str, treatment_id: str, inquiry_id: Optional[str] = None
) -> ItemizedQuote:
    provider = get_provider_by_id(provider_id)
    treatment = get_treatment_by_id(treatment_id)
    if not provider or not treatment:
        raise ValueError(f"Provider '{provider_id}' or Treatment '{treatment_id}' not found")

    hospital = get_hospital_by_id(provider.hospital_id)
    country = provider.country
    ratio = DESTINATION_COST_RATIOS.get(country, 0.35)

    # Base price calculation
    benchmark = treatment.us_benchmark_cost_usd
    estimated_total = round(benchmark * ratio, 2)

    # Itemized decomposition
    base_procedure = round(estimated_total * 0.45, 2)
    surgeon_fee = round(estimated_total * 0.25, 2)
    facility_stay = round(estimated_total * 0.20, 2)
    anesthesia_meds = round(estimated_total * 0.10, 2)
    total_package = base_procedure + surgeon_fee + facility_stay + anesthesia_meds

    # Explicitly disclosed included services
    included = [
        f"Pre-operative diagnostic workup & lab tests at {hospital.name if hospital else 'hospital'}",
        f"{treatment.typical_stay_days} nights private inpatient suite accommodation with attendant bed",
        "Primary surgeon, assistant surgeon, and anesthesiologist professional fees",
        "Implant/prosthetic hardware with manufacturer warranty certificate",
        "Physical therapy sessions and post-op mobility training while inpatient",
        "Airport VIP pickup and dedicated hospital transport",
        "24/7 dedicated bilingual medical concierge and translator",
        "Comprehensive medical record discharge summary & digital imaging transfer",
    ]

    # Explicitly disclosed potential additional expenses (Anti-surprise billing transparency)
    disclosed_extras = [
        "Extended ICU/inpatient stay beyond package duration ($350 - $600/night if clinically required)",
        "Specialized prescription medications after hospital discharge ($80 - $180)",
        "Post-discharge hotel stay during mandatory pre-flight recovery window ($55 - $120/night)",
        "International round-trip flights and attendant travel expenses",
        "Specialist second-opinion consultations for incidental non-target conditions",
    ]

    wait_days_map = {
        "India": 4,
        "Thailand": 6,
        "Turkey": 5,
        "United Arab Emirates": 3,
        "Singapore": 7,
    }
    wait_days = wait_days_map.get(country, 7)

    consult_avail_map = {
        "prov-tariq-ccad": "Next business day (Telehealth video available daily 14:00 - 18:00 GST)",
        "prov-ramesh-apollo": "Available within 48 hours (Telehealth video daily 10:00 - 14:00 IST)",
        "prov-somchai-bumrungrad": "Available within 72 hours (Telehealth video Tue/Thu 13:00 - 17:00 ICT)",
        "prov-murat-acibadem": "Available within 48 hours (Telehealth video Mon/Wed/Fri 11:00 - 15:00 TRT)",
    }

    aftercare_map = {
        "United Arab Emirates": "14 days local outpatient follow-up + 90 days telehealth check-ins included",
        "India": "10 days local physiotherapy + 180 days tele-rehabilitation monitoring",
        "Thailand": "12 days hotel nurse visits + 60 days continuous messaging with surgical team",
        "Turkey": "7 days local wound dressing visits + 90 days digital recovery tracking",
    }

    credentials_summary = (
        f"{', '.join(provider.credentials)} | {provider.years_experience} years experience | "
        f"{provider.successful_cases}+ verified cases | Rating: {provider.rating}/5.0"
    )

    return ItemizedQuote(
        inquiry_id=inquiry_id,
        provider_id=provider.id,
        provider_name=provider.name,
        hospital_id=provider.hospital_id,
        hospital_name=provider.hospital_name,
        treatment_name=treatment.name,
        country=provider.country,
        base_procedure_usd=base_procedure,
        surgeon_fee_usd=surgeon_fee,
        facility_stay_usd=facility_stay,
        anesthesia_meds_usd=anesthesia_meds,
        total_package_usd=total_package,
        included_services=included,
        disclosed_additional_expenses=disclosed_extras,
        consultation_availability=consult_avail_map.get(provider.id, "Within 3 business days"),
        estimated_waiting_days=wait_days,
        aftercare_arrangements=aftercare_map.get(country, "30-day digital telehealth follow-up included"),
        provider_qualifications_summary=credentials_summary,
    )


def compare_quotes_for_treatment(treatment_id: str) -> List[ItemizedQuote]:
    """Generates side-by-side transparent quote comparison for all providers offering the procedure."""
    treatment = get_treatment_by_id(treatment_id)
    if not treatment:
        raise ValueError(f"Treatment '{treatment_id}' not found")

    from medvoyage.catalog import PROVIDERS
    matching_providers = [p for p in PROVIDERS if p.specialty == treatment.category]
    # If category matches loosely, fallback to orthopedic providers for joint procedures
    if not matching_providers:
        matching_providers = PROVIDERS

    quotes = [build_transparent_quote(p.id, treatment_id) for p in matching_providers]
    return sorted(quotes, key=lambda q: q.total_package_usd)
