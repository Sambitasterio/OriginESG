# OriginESG — Emissions Tracking & Audit Platform

A full-stack Django REST + React application that ingests corporate emissions data from three real-world sources, normalises it to kg CO₂e, and provides an analyst review dashboard for approval, flagging, and audit locking.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-origin--esg.vercel.app-brightgreen?style=for-the-badge&logo=vercel)](https://origin-esg.vercel.app)
[![Backend API](https://img.shields.io/badge/Backend%20API-Railway-blueviolet?style=for-the-badge&logo=railway)](https://web-production-dfd6d.up.railway.app)

**Login credentials:** `user` / `user@123`

---

## What It Does

| Step | Description |
|------|-------------|
| **Ingest** | Upload SAP OData V4 JSON (Scope 1 fuel), Green Button CSV (Scope 2 electricity), or Concur Travel JSON (Scope 3 travel) |
| **Normalise** | Each parser converts raw values to kg CO₂e using DEFRA 2025 / EPA eGRID 2023 emission factors |
| **Review** | Analysts filter records by scope, source, and status; approve or flag with a comment |
| **Audit** | Every action is logged in an append-only ReviewAction trail; approved records can be locked |

---

## Architecture

```
Frontend (React + Vite)          Backend (Django REST Framework)
  Vercel                           Railway + PostgreSQL
  ├── /login                       ├── /api/token/          JWT auth
  ├── /                            ├── /api/datasources/    source list
  ├── /ingest                      ├── /api/ingest/sap/     SAP ingestion
  ├── /review                      ├── /api/ingest/utility/ CSV upload
  └── /review/:id                  ├── /api/ingest/travel/  Travel ingestion
                                   ├── /api/records/        review list
                                   ├── /api/records/:id/    detail
                                   └── /api/runs/           ingestion runs
```

**Data model (6 layers):**
```
Organization
  └── DataSource (SAP / UTILITY / TRAVEL)
        └── IngestionRun (each upload)
              └── RawRecord (immutable — exact input preserved)
                    └── NormalizedRecord (kg CO₂e, scope, status)
                          └── ReviewAction (append-only audit log)
```

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Django 4.x + Django REST Framework |
| Auth | djangorestframework-simplejwt |
| Database | PostgreSQL (Railway) |
| Frontend | React 18 + Vite + TypeScript |
| Styling | Tailwind CSS |
| Deployment | Railway (backend) + Vercel (frontend) |

---

## Local Development

### Prerequisites
- Python 3.12
- Node.js 18+

### Backend
```bash
cd backend
python -m venv ../venv
source ../venv/Scripts/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create backend/.env with your local database URL:
# DATABASE_URL=sqlite:///db.sqlite3
# SECRET_KEY=any-local-dev-secret
# DEBUG=True
# CORS_ALLOWED_ORIGINS=http://localhost:5173

python manage.py migrate
DJANGO_SUPERUSER_USERNAME=user DJANGO_SUPERUSER_PASSWORD=user@123 python init_db.py
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
# Create frontend/.env with: VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

---

## Sample Data

Three ready-to-use files in `/sample_data/`:

| File | Source | Rows |
|------|--------|------|
| `sap_odata_sample.json` | SAP OData V4 Purchase Orders | 10 valid + 2 missing-unit (expected fail) |
| `utility_greenbutton_sample.csv` | Green Button CSV | 6 rows, 2 meters, non-calendar billing periods |
| `concur_travel_sample.json` | Concur Itinerary JSON | 3 trips — domestic, international Business, missing cabin class |

---

## Key Design Decisions

- **RawRecord is immutable** — the original payload is stored as-is so any parsing bug can be corrected by re-running normalisation without losing source data.
- **Hard-fail on missing units** — a SAP row with no `OrderQuantityUnit` is rejected rather than guessed, surfacing the data quality issue explicitly.
- **Great-circle distance for flights** — haversine formula over OpenFlights.org airport coordinates, consistent with DEFRA 2025 methodology.
- **DEFRA 2025 factors** — all emission factors are pinned to a specific published version and stored on each NormalizedRecord so results are reproducible.

See [DECISIONS.md](DECISIONS.md), [TRADEOFFS.md](TRADEOFFS.md), and [SOURCES.md](SOURCES.md) for full reasoning.

---

## Repository Structure

```
├── backend/
│   ├── breathe_esg/        Django project settings, URLs
│   ├── ingestion/          Models, parsers, ingestion views
│   ├── organizations/      Organization + DataSource models
│   └── review/             NormalizedRecord review API
├── frontend/
│   └── src/
│       ├── pages/          LoginPage, DashboardPage, IngestPage, ReviewPage, RecordDetailPage
│       ├── api/            Axios client + typed endpoint functions
│       └── contexts/       AuthContext (JWT storage)
├── sample_data/            Test fixtures for all 3 sources
├── DECISIONS.md
├── TRADEOFFS.md
└── SOURCES.md
```
