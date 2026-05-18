# Walkthrough of the implementation

## Phase 0 — Project Setup & Infrastructure

### How to run the code

**Local (no Docker):**

```bash
# Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload          # → http://localhost:8000/docs

# Frontend (new terminal)
cd frontend && npm install
npm run dev                        # → http://localhost:5173/
```

**Docker:** `cp .env.example .env && docker compose up --build`

### What landed

- **00-01 Backend**: FastAPI skeleton (`backend/main.py`, `requirements.txt`, package tree under `app/`). `/health` and `/docs` return 200.
- **00-02 Frontend**: Vite + React + TS scaffold; `axios`, `react-router-dom`, `chart.js`, `react-chartjs-2` installed; `src/api/client.ts` with error interceptor.
- **00-03 Docker & env**: `.env.example`, `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`. `docker compose config` exits 0.

> **Note**: Validated on Python 3.13 (design specifies 3.12; the Docker image pins `python:3.12-slim`).

---

## Phase 1 — Database & Core Models

### What landed (Phase 1)

- **01-01 Database**: `backend/app/core/database.py` — SQLAlchemy 2.0 engine, `Base` (`DeclarativeBase`), `SessionLocal`, `get_db` dependency. SQLite file resolves to `backend/seo.db`.
- **01-02 ORM models** (6 tables): `registered_urls`, `scan_jobs`, `scan_results`, `lighthouse_audits` (FR-08 evidence), `improvement_suggestions` (FR-08 cache), `app_settings`.
- **01-03 Pydantic schemas**: `schemas/url.py`, `schemas/scan.py`, `schemas/result.py`, `schemas/suggestion.py` (incl. `AuditRecord`, `SuggestionRecord`, `SuggestionResponse`).

### How to verify

```bash
cd backend
.venv/bin/python -c "from app.core.database import engine; engine.connect(); print('OK')"
.venv/bin/python -c "from app.core.database import Base, engine; from app.models import url, scan_job, scan_result, lighthouse_audit, suggestion, settings; Base.metadata.create_all(engine); print('Tables created')"
.venv/bin/python -c "import sqlite3; print(sorted(r[0] for r in sqlite3.connect('seo.db').execute(\"SELECT name FROM sqlite_master WHERE type='table'\")))"
.venv/bin/python -c "from app.schemas.url import UrlCreate; print(UrlCreate(url='https://example.com'))"
```

Expected: the table list prints `['app_settings', 'improvement_suggestions', 'lighthouse_audits', 'registered_urls', 'scan_jobs', 'scan_results']`.

---

## Phase 2 — URL Management API

REST CRUD for the registered-URL list (02-01: `backend/app/api/urls.py`, 02-02: 5 pytest cases — all pass).

### How to manage URLs

Start the backend first:

```bash
cd backend && source .venv/bin/activate
uvicorn main:app --reload   # http://localhost:8000
```

Then, in another terminal:

```bash
# Register a URL (expect 201)
curl -X POST http://localhost:8000/api/urls \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/flights"}'

# Register the same URL again (expect 409: "This URL is already registered")
curl -X POST http://localhost:8000/api/urls \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/flights"}'

# List all registered URLs
curl http://localhost:8000/api/urls

# Delete a URL by id (expect 204; 404 if missing)
curl -X DELETE http://localhost:8000/api/urls/1
```

---

## Phase 3 — Scanner Service

`LighthouseAdapter` (03-01 ABC + 03-02 adapter + 03-03 4 passing tests) calls Google PageSpeed Insights v5 and returns 4 category scores, Core Web Vitals (LCP / INP / CLS), and per-audit detail.

### How to get Lighthouse metrics

Prerequisite: `PAGESPEED_API_KEY` set in `(project-root)/.env` (Google Cloud → APIs & Services → Credentials → PageSpeed Insights API key).

```bash
cd backend
set -a && . ../.env && set +a

.venv/bin/python -c "
from app.services.scanner.lighthouse import LighthouseAdapter
r = LighthouseAdapter().fetch_scores('https://YOUR-TARGET-URL')
print('Performance:   ', r.performance_score)
print('SEO:           ', r.seo_score)
print('Accessibility: ', r.accessibility_score)
print('Best Practices:', r.best_practices_score)
print('LCP (ms):      ', r.lcp_ms)
print('INP (ms):      ', r.inp_ms)
print('CLS:           ', r.cls)
print('Audits:        ', len(r.audits))
"
```

`INP` may be `None` if PSI has no field data for the URL — correct behavior per FR-03.

Run the unit tests: `cd backend && .venv/bin/pytest tests/test_scanner.py -v` (expect **4 passed**).
