"""Schema-based CSV and JSON catalog ingestion pipeline for treatments and providers."""

import csv
import io
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError
import medvoyage.catalog as cat
from medvoyage.models import Provider, Treatment
from medvoyage.storage import MedVoyageStorage


class IngestionError(Exception):
    pass


def ingest_treatments_json(
    json_content: str, storage: Optional[MedVoyageStorage] = None
) -> Tuple[List[Treatment], List[str]]:
    """Ingests a JSON array of treatment specifications and registers them in the catalog."""
    try:
        raw_list = json.loads(json_content)
    except Exception as e:
        raise IngestionError(f"Invalid JSON payload: {e}")

    if not isinstance(raw_list, list):
        raise IngestionError("JSON root must be a list of treatment objects")

    ingested = []
    errors = []
    for idx, item in enumerate(raw_list):
        try:
            treatment = Treatment.model_validate(item)
            # Update existing or append new in memory
            existing_idx = next((i for i, t in enumerate(cat.TREATMENTS) if t.id == treatment.id), None)
            if existing_idx is not None:
                cat.TREATMENTS[existing_idx] = treatment
            else:
                cat.TREATMENTS.append(treatment)
            # Persist to database if storage provided
            if storage:
                storage.save_treatment(treatment)
            ingested.append(treatment)
        except ValidationError as ve:
            errors.append(f"Row {idx} ({item.get('id', 'unknown')}): {ve.errors()}")

    return ingested, errors


def ingest_treatments_csv(
    csv_content: str, storage: Optional[MedVoyageStorage] = None
) -> Tuple[List[Treatment], List[str]]:
    """Ingests a CSV string containing treatment specifications and registers them in the catalog."""
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    ingested = []
    errors = []

    for idx, row in enumerate(reader, 1):
        try:
            item = {
                "id": row["id"].strip(),
                "category": row["category"].strip(),
                "name": row["name"].strip(),
                "description": row["description"].strip(),
                "typical_stay_days": int(row["typical_stay_days"]),
                "recovery_days": int(row["recovery_days"]),
                "us_benchmark_cost_usd": float(row["us_benchmark_cost_usd"]),
            }
            treatment = Treatment.model_validate(item)
            existing_idx = next((i for i, t in enumerate(cat.TREATMENTS) if t.id == treatment.id), None)
            if existing_idx is not None:
                cat.TREATMENTS[existing_idx] = treatment
            else:
                cat.TREATMENTS.append(treatment)
            if storage:
                storage.save_treatment(treatment)
            ingested.append(treatment)
        except Exception as e:
            errors.append(f"Line {idx}: {str(e)}")

    return ingested, errors


def ingest_providers_json(
    json_content: str, storage: Optional[MedVoyageStorage] = None
) -> Tuple[List[Provider], List[str]]:
    """Ingests a JSON array of provider specifications and registers them in the catalog."""
    try:
        raw_list = json.loads(json_content)
    except Exception as e:
        raise IngestionError(f"Invalid JSON payload: {e}")

    if not isinstance(raw_list, list):
        raise IngestionError("JSON root must be a list of provider objects")

    ingested = []
    errors = []
    for idx, item in enumerate(raw_list):
        try:
            provider = Provider.model_validate(item)
            existing_idx = next((i for i, p in enumerate(cat.PROVIDERS) if p.id == provider.id), None)
            if existing_idx is not None:
                cat.PROVIDERS[existing_idx] = provider
            else:
                cat.PROVIDERS.append(provider)
            if storage:
                storage.save_provider(provider)
            ingested.append(provider)
        except ValidationError as ve:
            errors.append(f"Row {idx} ({item.get('id', 'unknown')}): {ve.errors()}")

    return ingested, errors


def ingest_providers_csv(
    csv_content: str, storage: Optional[MedVoyageStorage] = None
) -> Tuple[List[Provider], List[str]]:
    """Ingests a CSV string containing provider specifications and registers them in the catalog."""
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    ingested = []
    errors = []

    for idx, row in enumerate(reader, 1):
        try:
            credentials = [c.strip() for c in row.get("credentials", "").split(";") if c.strip()]
            languages = [l.strip() for l in row.get("languages", "").split(";") if l.strip()]
            item = {
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                "title": row["title"].strip(),
                "specialty": row["specialty"].strip(),
                "hospital_id": row["hospital_id"].strip(),
                "hospital_name": row["hospital_name"].strip(),
                "country": row["country"].strip(),
                "city": row["city"].strip(),
                "years_experience": int(row["years_experience"]),
                "credentials": credentials,
                "languages": languages,
                "rating": float(row["rating"]),
                "verified": row.get("verified", "true").lower() in ("true", "1", "yes"),
                "successful_cases": int(row["successful_cases"]),
            }
            provider = Provider.model_validate(item)
            existing_idx = next((i for i, p in enumerate(cat.PROVIDERS) if p.id == provider.id), None)
            if existing_idx is not None:
                cat.PROVIDERS[existing_idx] = provider
            else:
                cat.PROVIDERS.append(provider)
            if storage:
                storage.save_provider(provider)
            ingested.append(provider)
        except Exception as e:
            errors.append(f"Line {idx}: {str(e)}")

    return ingested, errors
