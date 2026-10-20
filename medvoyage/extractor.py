"""Clinical record extraction engine for parsing unstructured discharge summaries and medical notes."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from medvoyage.catalog import TREATMENTS, get_treatment_by_id
from medvoyage.models import Urgency


class ExtractedClinicalInquiry(BaseModel):
    patient_name: Optional[str] = None
    patient_country: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    matched_treatment_id: str
    matched_treatment_name: str
    category: str
    clinical_diagnosis: str
    urgency: Urgency
    recommended_budget_usd: float
    key_findings: List[str] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list)
    surgical_alerts: List[str] = Field(default_factory=list)
    extracted_summary: str
    ready_for_inquiry: bool = True


# Clinical keyword mapping to treatments
CLINICAL_TREATMENT_MAP = [
    {
        "id": "knee-replacement",
        "keywords": [
            "knee",
            "gonarthrosis",
            "patellofemoral",
            "tibiofemoral",
            "tricompartmental",
            "knee osteoarthritis",
            "total knee arthroplasty",
            "tka",
        ],
        "budget": 16000.0,
    },
    {
        "id": "cabg-cardiac",
        "keywords": [
            "coronary artery",
            "cabg",
            "bypass graft",
            "angina",
            "ischemic heart",
            "lad stenosis",
            "triple vessel",
            "myocardial infarction",
        ],
        "budget": 24000.0,
    },
    {
        "id": "dental-all-on-4",
        "keywords": [
            "dental",
            "edentulous",
            "all-on-4",
            "all on 4",
            "dental implant",
            "maxillary bridge",
            "mandibular teeth",
            "periodontitis",
        ],
        "budget": 10500.0,
    },
    {
        "id": "hip-replacement",
        "keywords": [
            "hip",
            "coxarthrosis",
            "femoral head",
            "acetabular",
            "avascular necrosis",
            "hip osteoarthritis",
            "total hip arthroplasty",
            "tha",
        ],
        "budget": 18000.0,
    },
    {
        "id": "robotic-prostatectomy",
        "keywords": [
            "prostate",
            "psa elevated",
            "adenocarcinoma of prostate",
            "gleason",
            "da vinci",
            "radical prostatectomy",
        ],
        "budget": 22000.0,
    },
]


KNOWN_COUNTRIES = [
    "United States", "USA", "Canada", "United Kingdom", "UK", "Australia",
    "United Arab Emirates", "UAE", "Saudi Arabia", "Kuwait", "Qatar", "Oman",
    "Germany", "France", "Ireland", "New Zealand", "Singapore", "Turkey", "Thailand", "India"
]

MEDICAL_STOPWORDS = {
    "suffering", "acute", "severe", "chronic", "mild", "moderate", "pain",
    "osteoarthritis", "periodontitis", "knee", "hip", "stage", "tooth", "dental",
    "symptoms", "complications", "disease", "illness", "edema", "effusion", "stenosis"
}


def extract_clinical_inquiry(text: str) -> ExtractedClinicalInquiry:
    """Parses messy, unstructured discharge summaries or referral letters into structured inquiry parameters."""
    normalized_text = text.lower()

    # 1. Match Treatment against curated map and dynamic catalog
    best_treatment_id = "knee-replacement"
    highest_score = 0
    recommended_budget = 16000.0

    # Score against clinical keywords map
    for item in CLINICAL_TREATMENT_MAP:
        score = sum(3 for kw in item["keywords"] if kw in normalized_text)
        if score > highest_score:
            highest_score = score
            best_treatment_id = item["id"]
            recommended_budget = item["budget"]

    # Also score against any dynamically registered catalog treatments
    for t in TREATMENTS:
        t_tokens = [w for w in re.split(r"[\s\-_(),]+", t.name.lower()) if len(w) > 3]
        cat_tokens = [w for w in re.split(r"[\s\-_(),]+", t.category.lower()) if len(w) > 3]
        score = sum(2 for token in t_tokens if token in normalized_text)
        score += sum(1 for token in cat_tokens if token in normalized_text)
        if score > highest_score:
            highest_score = score
            best_treatment_id = t.id
            recommended_budget = round(t.us_benchmark_cost_usd * 0.40, 2)

    treatment = get_treatment_by_id(best_treatment_id)
    treatment_name = treatment.name if treatment else best_treatment_id
    category = treatment.category if treatment else "General Surgery"

    # 2. Extract Urgency
    if any(
        w in normalized_text
        for w in ["critical", "emergency", "unstable", "severe pain", "rapid progression", "urgent", "immediate"]
    ):
        urgency = Urgency.URGENT
    elif any(
        w in normalized_text
        for w in ["within month", "within 4 weeks", "next month", "4 to 6 weeks", "within the next", "4 weeks"]
    ):
        urgency = Urgency.WITHIN_MONTH
    elif any(w in normalized_text for w in ["flexible", "no rush", "whenever available", "asymptomatic"]):
        urgency = Urgency.FLEXIBLE
    else:
        urgency = Urgency.WITHIN_MONTH

    # 3. Extract Demographics via robust heuristics
    name_match = re.search(r"(?:patient\s+name|patient|name)[\s:]+([A-Za-z]+(?:[ \t]+[A-Za-z]+)+)", text, re.IGNORECASE)
    patient_name = name_match.group(1).strip() if name_match else "International Patient"

    # Age extraction supporting: '49yo', '49 yo', '58 years old', 'Age: 55'
    patient_age = None
    age_prefix_match = re.search(r"\b(\d{1,3})[\s-]*(?:yo|y\.?o\.?|years?[\s-]old)\b", text, re.IGNORECASE)
    if age_prefix_match:
        val = int(age_prefix_match.group(1))
        if 0 < val < 125:
            patient_age = val
    if patient_age is None:
        age_header_match = re.search(r"\b(?:age|aged)[\s:]*(\d{1,3})\b", text, re.IGNORECASE)
        if age_header_match:
            val = int(age_header_match.group(1))
            if 0 < val < 125:
                patient_age = val

    # Gender extraction: check explicit fields first before narrative pronouns
    gender = None
    explicit_gender = re.search(r"\b(?:gender|sex)[\s:]*(male|female|m\b|f\b)\b", text, re.IGNORECASE)
    if explicit_gender:
        g_val = explicit_gender.group(1).lower()
        gender = "Female" if g_val in ("female", "f") else "Male"
    else:
        patient_subject_match = re.search(r"\b\d{1,3}[\s-]*(?:yo|years?[\s-]old)[\s,]+(female|woman|male|man)\b", text, re.IGNORECASE)
        if patient_subject_match:
            g_val = patient_subject_match.group(1).lower()
            gender = "Female" if g_val in ("female", "woman") else "Male"
        elif re.search(r"\b(mr\.)\s+[A-Z]", text, re.IGNORECASE):
            gender = "Male"
        elif re.search(r"\b(ms\.|mrs\.)\s+[A-Z]", text, re.IGNORECASE):
            gender = "Female"
        else:
            female_count = len(re.findall(r"\b(female|woman|she|her)\b", text, re.IGNORECASE))
            male_count = len(re.findall(r"\b(male|man|he|his)\b", text, re.IGNORECASE))
            if female_count > male_count:
                gender = "Female"
            elif male_count > female_count:
                gender = "Male"

    # Country extraction: check explicit origin labels and filter out medical symptoms
    patient_country = None
    country_header = re.search(
        r"(?:country(?:\s+of\s+residence)?|residence|traveling\s+from|travels\s+from|patient\s+origin)[\s:]+([A-Za-z]+(?:[ \t]+[A-Za-z]+)*)",
        text,
        re.IGNORECASE,
    )
    if country_header:
        cand = country_header.group(1).strip()
        words = cand.lower().split()
        if not any(w in MEDICAL_STOPWORDS for w in words):
            patient_country = cand

    if not patient_country:
        # Search for known countries mentioned with 'from <Country>' or in text
        for country in KNOWN_COUNTRIES:
            pattern = rf"\b(?:from|in|traveling\s+from)?\s*({re.escape(country)})\b"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                patient_country = country
                break

    if not patient_country:
        patient_country = "United States"

    # 4. Extract Findings and Comorbidities
    findings = []
    if "osteoarthritis" in normalized_text or "degeneration" in normalized_text:
        findings.append("Severe degenerative joint space narrowing")
    if "stenosis" in normalized_text:
        findings.append("Vascular luminal stenosis documented on imaging")
    if "mri" in normalized_text or "x-ray" in normalized_text or "ct scan" in normalized_text:
        findings.append("Radiographic imaging available for surgeon pre-evaluation")
    if not findings:
        findings.append("Clinical evaluation consistent with advanced structural disease")

    comorbidities = []
    if "hypertension" in normalized_text or "htn" in normalized_text:
        comorbidities.append("Hypertension")
    if "diabetes" in normalized_text or "dm2" in normalized_text:
        comorbidities.append("Type 2 Diabetes Mellitus")
    if "asthma" in normalized_text or "copd" in normalized_text:
        comorbidities.append("Respiratory Comorbidity")

    alerts = []
    if "anticoagulant" in normalized_text or "aspirin" in normalized_text or "warfarin" in normalized_text:
        alerts.append("Patient on anticoagulant therapy; peri-operative bridging required")
    if "allergy" in normalized_text or "allergic" in normalized_text:
        alerts.append("Reported allergies documented on medical record")

    # 5. Extract Diagnosis
    diag_match = re.search(r"(?:diagnosis|impression|assessment)[\s:]+([^\.\n]+)", text, re.IGNORECASE)
    clinical_diagnosis = (
        diag_match.group(1).strip()
        if diag_match
        else f"Indication for {treatment_name} based on clinical discharge summary."
    )

    summary_text = (
        f"{patient_name} ({patient_age or 'Adult'}yo {gender or ''}) presents with {clinical_diagnosis}. "
        f"Evaluated for international {treatment_name}. "
        f"Comorbidities: {', '.join(comorbidities) if comorbidities else 'None reported'}."
    )

    return ExtractedClinicalInquiry(
        patient_name=patient_name,
        patient_country=patient_country,
        patient_age=patient_age,
        patient_gender=gender,
        matched_treatment_id=best_treatment_id,
        matched_treatment_name=treatment_name,
        category=category,
        clinical_diagnosis=clinical_diagnosis,
        urgency=urgency,
        recommended_budget_usd=recommended_budget,
        key_findings=findings,
        comorbidities=comorbidities,
        surgical_alerts=alerts,
        extracted_summary=summary_text,
        ready_for_inquiry=True,
    )
