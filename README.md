# MedVoyage

> **EthAum Venture Partners | Medical Tourism Platform Challenge**  
> **Track**: Web Development / Healthcare Marketplace  
> **Submission Deadline**: 11 November 2026 (Registration Verified: 19 October 2026)  
> **Pinned Runtime**: Python 3.13 (`.python-version`)

MedVoyage is an AI-powered medical tourism marketplace designed to eliminate pricing opacity, build cross-border trust, and provide continuous aftercare for international patients seeking high-acuity surgical care.

---

## 🌟 The Core Differentiator: Transparent Treatment Comparison
Rather than building an opaque hospital directory with misleading "prices starting from" teaser rates, MedVoyage decomposes every procedure package into full itemized clarity:

- **Estimated Total Package Cost**: Clear, benchmarked rates with up to 75% savings compared to US/UK private care.
- **Included Services (Explicitly Listed)**: Pre-op diagnostics, surgeon fees, private hospital suites, anesthesia, implant hardware, dedicated medical concierge, and airport transfers.
- **Disclosed Potential Additional Expenses (Anti-Surprise Billing)**: Upfront disclosure of costs for extended ICU stays, post-discharge medications, and mandatory recovery hotel nights.
- **Consultation Availability**: Real-time telehealth video appointment slots with operating surgeons.
- **Estimated Waiting Times**: Direct scheduling transparency (typically 3 to 7 days).
- **Structured Aftercare**: 90-day continuous recovery plans with remote surgical check-ins.
- **Verifiable Provider Credentials**: JCI accreditation records, board certifications (FRCS, American Board, EBOT), surgical volume statistics, and complication rates.
- **Clinical Discharge NLP Extractor**: Automatically parses freeform clinical notes, surgical histories, and referral letters into structured inquiry parameters.
- **Schema-Based Catalog Ingestion**: Supports bulk CSV and JSON ingestion for treatments and hospitals with strict Pydantic validation.
- **SQLite Persistence & API Security**: Persistent database storage across server restarts (`MEDVOYAGE_DB_PATH`) and `X-API-Key` authentication.

---

## 🚀 Quickstart & Setup

### 1. Local Installation
```bash
cd medvoyage

# Install dependencies
pip install -r requirements.txt

# Run the full automated test suite
python -m pytest

# Launch the MedVoyage marketplace server
uvicorn medvoyage.api:app --reload --port 8000
```

Open the marketplace web interface in your browser: `http://localhost:8000/`  
Open the interactive Swagger API documentation: `http://localhost:8000/docs`

---

## 🧪 Testing

Run all 25 automated unit and integration tests verifying matching, pricing, NLP extraction, catalog ingestion, and SQLite persistence:
```bash
python -m pytest
```

Output:
```text
tests/test_api.py .....
tests/test_auth_and_security.py .
tests/test_booking_and_aftercare.py .
tests/test_catalog.py ..
tests/test_catalog_ingestion.py ....
tests/test_matcher.py ..
tests/test_medical_record_extractor.py .....
tests/test_models.py ..
tests/test_quote_engine.py ..
tests/test_sqlite_persistence.py .
============================= 25 passed in 0.56s =============================
```

---

## 🐳 Docker Deployment

```bash
# Build the production Docker image (runs tests automatically during build)
docker build -t medvoyage-marketplace .

# Run the container
docker run -p 8000:8000 medvoyage-marketplace
```

---

## 📁 Repository Structure

```
medvoyage/
├── .gitignore
├── .python-version               # Pinned Python 3.13 runtime
├── Dockerfile                    # Production container
├── README.md                     # Project overview and setup instructions
├── requirements.txt              # Pinned Python dependencies
├── docs/
│   ├── BENCHMARK_REPORT.md       # In-depth market research & competitor analysis
│   ├── DEMO_SCRIPT.md            # Video walkthrough script for judges
│   ├── MARKETPLACE_STRATEGY.md   # Commercial strategy & monetization framework
│   └── TEAM_PROFILES.md          # Team LinkedIn profiles & contributor bios
├── medvoyage/
│   ├── __init__.py
│   ├── aftercare.py              # 90-day post-op recovery tracking engine
│   ├── api.py                    # REST API & responsive HTML marketplace UI
│   ├── booking.py                # Telehealth consultation scheduling manager
│   ├── catalog.py                # Curated destinations, treatments, hospitals & providers
│   ├── matcher.py                # AI provider matching algorithm
│   ├── models.py                 # Pydantic schemas (Inquiry, Quote, Provider, Booking)
│   ├── quote_engine.py           # Transparent itemized quote generation engine
│   └── sample_data.py            # Pre-seeded marketplace inquiries & bookings
└── tests/
    ├── __init__.py
    ├── test_api.py               # REST endpoints & HTML view tests
    ├── test_booking_and_aftercare.py # Booking & milestone progression tests
    ├── test_catalog.py           # Catalog data validation tests
    ├── test_matcher.py           # AI matching algorithm validation
    ├── test_models.py            # Model serialization tests
    └── test_quote_engine.py      # Price decomposition & transparency tests
```

---

## 📑 EthAum Venture Partners Deliverables
- **Market Research & Benchmarking**: See [`docs/BENCHMARK_REPORT.md`](docs/BENCHMARK_REPORT.md)
- **Marketplace Business Strategy**: See [`docs/MARKETPLACE_STRATEGY.md`](docs/MARKETPLACE_STRATEGY.md)
- **Judges Demonstration Script**: See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
- **Team LinkedIn Profiles**: See [`docs/TEAM_PROFILES.md`](docs/TEAM_PROFILES.md)
