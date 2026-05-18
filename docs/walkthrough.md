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

### What landed (Phase 2)

- **02-01 URL CRUD**: `backend/app/api/urls.py` — `GET /api/urls`, `POST /api/urls` (201, duplicate → 409 with `"This URL is already registered"`), `DELETE /api/urls/{id}` (204 / 404). Router wired into `main.py`; ORM models registered with `Base.metadata` on import.
- **02-02 Unit tests**: `backend/tests/test_urls.py` — 5 cases (201, 409, 422, 204, 404) using `TestClient` + in-memory SQLite via shared-pool dependency override.

### How to verify (Phase 2)

```bash
cd backend
.venv/bin/pytest tests/test_urls.py -v   # 5 passed

# Live curl (requires uvicorn running):
curl -X POST http://localhost:8000/api/urls -d '{"url":"https://example.com/flights"}' -H "Content-Type: application/json"   # 201
curl -X POST http://localhost:8000/api/urls -d '{"url":"https://example.com/flights"}' -H "Content-Type: application/json"   # 409
curl -X DELETE http://localhost:8000/api/urls/1                                                                              # 204
curl -X DELETE http://localhost:8000/api/urls/99999                                                                          # 404
```
