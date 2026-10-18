"""Tests for MedVoyage quote engine and transparent pricing."""

import pytest
from medvoyage.quote_engine import build_transparent_quote, compare_quotes_for_treatment


def test_quote_generation_and_transparency():
    quote = build_transparent_quote(
        provider_id="prov-tariq-ccad", treatment_id="knee-replacement"
    )
    assert quote.country == "United Arab Emirates"
    assert quote.total_package_usd > 0
    # Package sum should equal individual line items
    calculated_sum = (
        quote.base_procedure_usd
        + quote.surgeon_fee_usd
        + quote.facility_stay_usd
        + quote.anesthesia_meds_usd
    )
    assert round(quote.total_package_usd, 2) == round(calculated_sum, 2)

    # Must contain explicitly included services and disclosed additional expenses
    assert len(quote.included_services) >= 5
    assert len(quote.disclosed_additional_expenses) >= 3
    assert quote.estimated_waiting_days > 0
    assert len(quote.aftercare_arrangements) > 0


def test_compare_quotes_sorting():
    quotes = compare_quotes_for_treatment("knee-replacement")
    assert len(quotes) >= 3
    # Quotes must be sorted ascending by total package price
    for i in range(len(quotes) - 1):
        assert quotes[i].total_package_usd <= quotes[i + 1].total_package_usd
