"""Curated catalog of destinations, treatments, hospitals, and credentialed providers."""

from typing import List, Optional
from medvoyage.models import Destination, Hospital, Provider, Treatment

DESTINATIONS: List[Destination] = [
    Destination(
        id="uae-abu-dhabi",
        country="United Arab Emirates",
        city="Abu Dhabi",
        description="Global healthcare capital with world-leading Cleveland Clinic and CCAD centers.",
        visa_policy="Medical tourism visa issued within 48 hours; visa-free for 70+ nations.",
        international_hub="AUH (Abu Dhabi International Airport)",
        average_hotel_cost_usd_per_night=120.0,
        jci_hospitals_count=18,
    ),
    Destination(
        id="india-chennai",
        country="India",
        city="Chennai",
        description="Renowned as India's medical capital; benchmark cardiac and orthopedic centers.",
        visa_policy="e-Medical Visa available online with fast-track entry for patient and 2 attendants.",
        international_hub="MAA (Chennai International Airport)",
        average_hotel_cost_usd_per_night=55.0,
        jci_hospitals_count=12,
    ),
    Destination(
        id="thailand-bangkok",
        country="Thailand",
        city="Bangkok",
        description="Southeast Asia's premier medical hub; world-renowned hospitality and accredited clinics.",
        visa_policy="60-day medical visa on arrival for international patients.",
        international_hub="BKK (Suvarnabhumi Airport)",
        average_hotel_cost_usd_per_night=65.0,
        jci_hospitals_count=30,
    ),
    Destination(
        id="turkey-istanbul",
        country="Turkey",
        city="Istanbul",
        description="Crossroads of medical excellence, advanced oncology, cosmetic and dental care.",
        visa_policy="Fast eVisa or visa waiver for European, GCC, and North American travelers.",
        international_hub="IST (Istanbul Airport)",
        average_hotel_cost_usd_per_night=70.0,
        jci_hospitals_count=26,
    ),
    Destination(
        id="singapore-sg",
        country="Singapore",
        city="Singapore",
        description="Gold standard clinical governance, robotic surgery, and precision oncology.",
        visa_policy="Medical referral electronic travel authorization.",
        international_hub="SIN (Changi Airport)",
        average_hotel_cost_usd_per_night=180.0,
        jci_hospitals_count=15,
    ),
]

TREATMENTS: List[Treatment] = [
    Treatment(
        id="knee-replacement",
        category="Orthopedics",
        name="Total Knee Replacement (Minimally Invasive)",
        description="Complete prosthetic resurfacing of femoral and tibial components with computer navigation.",
        typical_stay_days=5,
        recovery_days=21,
        us_benchmark_cost_usd=38000.0,
    ),
    Treatment(
        id="cabg-cardiac",
        category="Cardiology",
        name="Coronary Artery Bypass Graft (CABG)",
        description="Off-pump beating heart bypass graft using arterial conduits.",
        typical_stay_days=7,
        recovery_days=30,
        us_benchmark_cost_usd=120000.0,
    ),
    Treatment(
        id="dental-all-on-4",
        category="Dental",
        name="All-on-4 Full Arch Dental Implants",
        description="Immediate load titanium implants with fixed zirconium prosthetic bridge.",
        typical_stay_days=4,
        recovery_days=10,
        us_benchmark_cost_usd=28000.0,
    ),
    Treatment(
        id="hip-replacement",
        category="Orthopedics",
        name="Anterior Hip Replacement (Muscle-Sparing)",
        description="Direct anterior approach preserving gluteal muscle attachments for rapid rehabilitation.",
        typical_stay_days=4,
        recovery_days=18,
        us_benchmark_cost_usd=42000.0,
    ),
    Treatment(
        id="robotic-prostatectomy",
        category="Oncology & Urology",
        name="Da Vinci Robotic Radical Prostatectomy",
        description="Nerve-sparing robotic oncological resection for localized prostate cancer.",
        typical_stay_days=3,
        recovery_days=14,
        us_benchmark_cost_usd=55000.0,
    ),
]

HOSPITALS: List[Hospital] = [
    Hospital(
        id="hosp-ccad-auh",
        name="Cleveland Clinic Abu Dhabi",
        country="United Arab Emirates",
        city="Abu Dhabi",
        jci_accredited=True,
        established_year=2015,
        bed_count=364,
        international_patient_concierge=True,
        airport_transfer_included=True,
        translators_available=["English", "Arabic", "Russian", "French"],
    ),
    Hospital(
        id="hosp-apollo-chennai",
        name="Apollo Hospitals Greams Road",
        country="India",
        city="Chennai",
        jci_accredited=True,
        established_year=1983,
        bed_count=600,
        international_patient_concierge=True,
        airport_transfer_included=True,
        translators_available=["English", "Arabic", "Russian", "Hindi"],
    ),
    Hospital(
        id="hosp-bumrungrad-bkk",
        name="Bumrungrad International Hospital",
        country="Thailand",
        city="Bangkok",
        jci_accredited=True,
        established_year=1980,
        bed_count=580,
        international_patient_concierge=True,
        airport_transfer_included=True,
        translators_available=["English", "Arabic", "Japanese", "German"],
    ),
    Hospital(
        id="hosp-acibadem-ist",
        name="Acibadem Maslak Hospital",
        country="Turkey",
        city="Istanbul",
        jci_accredited=True,
        established_year=2009,
        bed_count=360,
        international_patient_concierge=True,
        airport_transfer_included=True,
        translators_available=["English", "Arabic", "Russian", "Turkish"],
    ),
]

PROVIDERS: List[Provider] = [
    Provider(
        id="prov-tariq-ccad",
        name="Dr. Tariq Al-Otaiba",
        title="Consultant Orthopedic Surgeon",
        specialty="Orthopedics",
        hospital_id="hosp-ccad-auh",
        hospital_name="Cleveland Clinic Abu Dhabi",
        country="United Arab Emirates",
        city="Abu Dhabi",
        years_experience=18,
        credentials=["FRCS (Tr & Orth) UK", "American Board of Orthopaedic Surgery", "JCI Certified Specialist"],
        languages=["English", "Arabic"],
        rating=4.95,
        verified=True,
        successful_cases=1240,
    ),
    Provider(
        id="prov-ramesh-apollo",
        name="Dr. Ramesh Sundaram",
        title="Senior Director of Joint Reconstruction",
        specialty="Orthopedics",
        hospital_id="hosp-apollo-chennai",
        hospital_name="Apollo Hospitals Greams Road",
        country="India",
        city="Chennai",
        years_experience=24,
        credentials=["FRCS Glasgow", "MCh Orth Liverpool", "Pioneer in Navigation Joint Replacement"],
        languages=["English", "Tamil", "Hindi"],
        rating=4.92,
        verified=True,
        successful_cases=3100,
    ),
    Provider(
        id="prov-somchai-bumrungrad",
        name="Dr. Somchai Charoenwong",
        title="Chief of Arthroplasty & Sports Medicine",
        specialty="Orthopedics",
        hospital_id="hosp-bumrungrad-bkk",
        hospital_name="Bumrungrad International Hospital",
        country="Thailand",
        city="Bangkok",
        years_experience=20,
        credentials=["MD Chulalongkorn", "Fellowship Harvard Medical School", "American Academy of Orthopaedic Surgeons"],
        languages=["English", "Thai"],
        rating=4.89,
        verified=True,
        successful_cases=2450,
    ),
    Provider(
        id="prov-murat-acibadem",
        name="Dr. Murat Demir",
        title="Head of Adult Joint Replacement",
        specialty="Orthopedics",
        hospital_id="hosp-acibadem-ist",
        hospital_name="Acibadem Maslak Hospital",
        country="Turkey",
        city="Istanbul",
        years_experience=16,
        credentials=["European Board of Orthopaedics (EBOT)", "Fellowship Mayo Clinic"],
        languages=["English", "Turkish", "Russian"],
        rating=4.87,
        verified=True,
        successful_cases=1800,
    ),
]


def get_treatment_by_id(tid: str) -> Optional[Treatment]:
    return next((t for t in TREATMENTS if t.id == tid), None)


def get_provider_by_id(pid: str) -> Optional[Provider]:
    return next((p for p in PROVIDERS if p.id == pid), None)


def get_hospital_by_id(hid: str) -> Optional[Hospital]:
    return next((h for h in HOSPITALS if h.id == hid), None)


def get_destination_by_id(did: str) -> Optional[Destination]:
    return next((d for d in DESTINATIONS if d.id == did), None)
