"""AI-assisted provider matching engine for MedVoyage."""

from typing import List
from medvoyage.catalog import PROVIDERS, get_hospital_by_id, get_provider_by_id, get_treatment_by_id
from medvoyage.models import MatchScore, PatientInquiry, Urgency
from medvoyage.quote_engine import build_transparent_quote


def match_providers_for_inquiry(inquiry: PatientInquiry) -> List[MatchScore]:
    treatment = get_treatment_by_id(inquiry.treatment_id)
    if not treatment:
        return []

    scores: List[MatchScore] = []

    for provider in PROVIDERS:
        hospital = get_hospital_by_id(provider.hospital_id)
        quote = build_transparent_quote(provider.id, inquiry.treatment_id, inquiry_id=inquiry.id)

        # 1. Clinical Fit Score (Weight: 40%)
        # Experience, rating, verified case volume, specialty match
        specialty_match = 1.0 if provider.specialty == treatment.category else 0.8
        experience_factor = min(provider.years_experience / 25.0, 1.0)
        rating_factor = (provider.rating - 4.0) / 1.0  # e.g., 4.95 -> 0.95
        cases_factor = min(provider.successful_cases / 3000.0, 1.0)
        clinical_score = round(
            (specialty_match * 0.4 + experience_factor * 0.2 + rating_factor * 0.2 + cases_factor * 0.2) * 100.0,
            1,
        )

        # 2. Budget Fit Score (Weight: 35%)
        # Packages within patient's stated budget receive high score
        if inquiry.budget_usd <= 0:
            budget_score = 80.0
        elif quote.total_package_usd <= inquiry.budget_usd:
            # Within budget: fully affordable
            budget_score = 95.0
        else:
            # Over budget: penalize proportionately
            over_pct = (quote.total_package_usd - inquiry.budget_usd) / inquiry.budget_usd
            budget_score = round(max(20.0, 80.0 - over_pct * 120.0), 1)

        # 3. Logistics & Preference Score (Weight: 30%)
        # Destination preference, language support, urgency vs waiting days
        dest_match = 1.0
        if inquiry.preferred_destinations:
            is_preferred = (
                provider.country in inquiry.preferred_destinations
                or (hospital and hospital.city in inquiry.preferred_destinations)
            )
            dest_match = 1.0 if is_preferred else 0.15

        lang_match = 1.0 if inquiry.preferred_language.capitalize() in provider.languages or (hospital and inquiry.preferred_language.capitalize() in hospital.translators_available) else 0.7

        urgency_match = 1.0
        if inquiry.urgency == Urgency.URGENT and quote.estimated_waiting_days > 4:
            urgency_match = 0.6

        logistics_score = round((dest_match * 0.5 + lang_match * 0.3 + urgency_match * 0.2) * 100.0, 1)

        # Total Composite Weighted Score
        total_score = round(
            clinical_score * 0.40 + budget_score * 0.35 + logistics_score * 0.25,
            1,
        )

        # Generate intelligent rationale
        rationale = (
            f"{provider.name} at {hospital.name} ({provider.country}) scored {total_score}/100. "
            f"Package of ${quote.total_package_usd:,.0f} vs your budget of ${inquiry.budget_usd:,.0f}. "
            f"Wait time is {quote.estimated_waiting_days} days. {provider.years_experience} years surgical tenure "
            f"with {provider.successful_cases}+ verified procedures."
        )

        scores.append(
            MatchScore(
                provider_id=provider.id,
                provider_name=provider.name,
                hospital_name=hospital.name,
                country=provider.country,
                total_score=total_score,
                clinical_score=clinical_score,
                budget_score=budget_score,
                logistics_score=logistics_score,
                rationale=rationale,
                estimated_quote_usd=quote.total_package_usd,
            )
        )

    return sorted(scores, key=lambda s: s.total_score, reverse=True)
