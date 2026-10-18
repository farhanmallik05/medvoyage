"""Tests for MedVoyage destination, treatment, and provider catalog."""

from medvoyage.catalog import (
    DESTINATIONS,
    HOSPITALS,
    PROVIDERS,
    TREATMENTS,
    get_destination_by_id,
    get_hospital_by_id,
    get_provider_by_id,
    get_treatment_by_id,
)


def test_catalog_integrity():
    assert len(DESTINATIONS) >= 4
    assert len(TREATMENTS) >= 4
    assert len(HOSPITALS) >= 4
    assert len(PROVIDERS) >= 4

    # All hospitals should have JCI accreditation in this premium catalog
    assert all(h.jci_accredited for h in HOSPITALS)

    # All providers should be verified and have credentials
    assert all(p.verified and len(p.credentials) > 0 for p in PROVIDERS)


def test_lookups():
    t = get_treatment_by_id("knee-replacement")
    assert t is not None
    assert t.category == "Orthopedics"

    p = get_provider_by_id("prov-tariq-ccad")
    assert p is not None
    assert "Cleveland Clinic" in p.hospital_name

    d = get_destination_by_id("uae-abu-dhabi")
    assert d is not None
    assert d.country == "United Arab Emirates"
