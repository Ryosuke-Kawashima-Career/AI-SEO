# Implementation Plan

> **Source**: [design.md](design.md)
> **Status**: Draft
> **Last Updated**: 2026-05-18

---

## Conventions

- **State labels**: `[todo]` → `[doing]` → `[done]`
- **Step ID format**: `PHASE-STEP` (e.g., `02-01` = Phase 2, Step 1)
- **Verification**: Every step must be verified by the listed command or UI check before marking `[done]`
- **Dependency rule**: Never start a step until all steps it depends on are `[done]`

---

## Dependency Graph

```text
Phase 0 (Setup)
  └── Phase 1 (DB & Models)
        └── Phase 2 (URL Management API)
              └── Phase 3 (Scanner Service)
                    └── Phase 4 (Scan Runner & Job API)
                          ├── Phase 5 (Scheduler)
                          └── Phase 6 (Results API)
                                └── Phase 7 (Suggester Service & API)        ★ FR-08 backend
                                      └── Phase 8 (Frontend Foundation)
                                            └── Phase 9 (Layout)
                                                  ├── Phase 10 (Dashboard)
                                                  ├── Phase 11 (URL Manager)
                                                  ├── Phase 12 (History)
                                                  ├── Phase 13 (Compare)
                                                  ├── Phase 14 (Suggestions) ★ FR-08 frontend
                                                  └── Phase 15 (Settings)
                                                        └── Phase 16 (Email Notifier) *
                                                              └── Phase 17 (Integration & Polish)

* Phase 16 minimum code dependencies: Phase 0 (env vars) + Phase 4 (Scan Runner).
  Scheduled after the Suggestions phase because FR-08 has higher business priority than FR-06's email notification.
```

---

## Phase 0 — Project Setup & Infrastructure

### 00-01 — Initialize backend project structure `[done]`

- **Design ref**: Section 8 (Directory Structure)
- **Files to create**:
  - `backend/main.py`
  - `backend/requirements.txt`
  - `backend/app/__init__.py`
  - `backend/app/api/__init__.py`
  - `backend/app/core/__init__.py`
  - `backend/app/models/__init__.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/services/__init__.py`
  - `backend/app/services/scanner/__init__.py`
  - `backend/app/services/suggester/__init__.py`
- **Acceptance Criteria**: `cd backend && python -m uvicorn main:app` starts without import errors
- **Verification**: `curl http://localhost:8000/docs` returns HTTP 200

---

### 00-02 — Initialize frontend project structure `[done]`

- **Depends on**: —
- **Design ref**: Section 8 (Directory Structure)
- **Command**: `npm create vite@latest frontend -- --template react-ts`
- **Additional packages**: `npm install axios react-router-dom chart.js react-chartjs-2`
- **Files to create**:
  - `frontend/src/api/client.ts`
  - `frontend/src/pages/.gitkeep`
  - `frontend/src/components/.gitkeep`
- **Acceptance Criteria**: `cd frontend && npm run dev` serves the Vite default page on `localhost:5173`
- **Verification**: Browser shows Vite + React splash screen

---

### 00-03 — Create Docker & environment configuration `[done]`

- **Depends on**: 00-01, 00-02
- **Design ref**: Section 2 (Technology Stack — Containerization)
- **Files to create**:
  - `.env.example` — variables: `PAGESPEED_API_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ADMIN_EMAIL`
  - `docker-compose.yml` — services: `backend` (port 8000), `frontend` (port 5173)
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
- **Acceptance Criteria**: `docker-compose up --build` starts both services without errors
- **Verification**: `curl http://localhost:8000/docs` and `curl http://localhost:5173` both return HTTP 200

---

## Phase 1 — Database & Core Models

### 01-01 — Set up SQLAlchemy + SQLite connection `[done]`

- **Depends on**: 00-01
- **Design ref**: Section 6 (Data Schema), Section 8
- **Files to create/modify**:
  - `backend/app/core/database.py` — engine, `SessionLocal`, `Base`, `get_db` dependency
- **Acceptance Criteria**: Importing `from app.core.database import Base` succeeds; `engine.connect()` creates `seo.db` file
- **Verification**: `python -c "from app.core.database import engine; engine.connect(); print('OK')"`

---

### 01-02 — Create ORM models `[done]`

- **Depends on**: 01-01
- **Design ref**: Section 6 (ER Diagram)
- **Files to create**:
  - `backend/app/models/url.py` — `RegisteredUrl` (id, url UNIQUE, label, created_at, updated_at)
  - `backend/app/models/scan_job.py` — `ScanJob` (id, triggered_by, started_at, completed_at, total_urls, success_count, failure_count, status)
  - `backend/app/models/scan_result.py` — `ScanResult` (id, url_id FK, job_id FK, scanned_at, performance_score, seo_score, accessibility_score, best_practices_score, lcp_ms, inp_ms, cls, status, error_reason, retry_count)
  - `backend/app/models/lighthouse_audit.py` — `LighthouseAudit` (id, scan_result_id FK, audit_id, title, category, score, display_value) — **FR-08 evidence**
  - `backend/app/models/suggestion.py` — `ImprovementSuggestion` (id, url_id FK, scan_result_id FK, audit_id, affected_dimension, action_description, estimated_impact, confidence_level, rank, generated_at) — **FR-08 cache**
  - `backend/app/models/settings.py` — `AppSettings` (id=1 singleton, scan_frequency, scan_time_utc, admin_email, updated_at)
- **Acceptance Criteria**: `Base.metadata.create_all(engine)` creates all 6 tables in `seo.db`
- **Verification**: `python -c "from app.core.database import Base, engine; from app.models import url, scan_job, scan_result, lighthouse_audit, suggestion, settings; Base.metadata.create_all(engine); print('Tables created')"` exits without error

---

### 01-03 — Create Pydantic schemas `[done]`

- **Depends on**: 01-02
- **Design ref**: Section 7 (API Design — request/response bodies)
- **Files to create**:
  - `backend/app/schemas/url.py` — `UrlCreate`, `UrlResponse`
  - `backend/app/schemas/scan.py` — `ScanJobResponse`, `TriggerScanResponse`
  - `backend/app/schemas/result.py` — `ScanResultResponse`, `LatestResultResponse`, `ComparisonResultResponse`, `AppSettingsResponse`, `AppSettingsUpdate`
  - `backend/app/schemas/suggestion.py` — `AuditRecord`, `SuggestionRecord`, `SuggestionResponse` (matches Section 7 — Suggestions JSON schema)
- **Acceptance Criteria**: All schema classes import without error; `UrlCreate(url="https://example.com")` instantiates correctly
- **Verification**: `python -c "from app.schemas.url import UrlCreate; from app.schemas.suggestion import SuggestionRecord; print('OK')"`

---

## Phase 2 — URL Management API

### 02-01 — Implement URL CRUD endpoints `[done]`

- **Depends on**: 01-02, 01-03
- **Design ref**: Section 7 (URL Management — FR-01)
- **FR**: FR-01
- **Files to create**:
  - `backend/app/api/urls.py` — `GET /api/urls`, `POST /api/urls`, `DELETE /api/urls/{id}`
- **Logic**:
  - `POST /api/urls`: validate URL format (`http://` or `https://`); reject duplicate with HTTP 409 and message `"This URL is already registered"`; persist to DB; return 201
  - `DELETE /api/urls/{id}`: return 404 if not found; return 204 on success
- **AC ref**: AC-01 (URL Registration), AC-02 (Duplicate URL Rejection)
- **Verification**:

  ```bash
  # Register
  curl -X POST http://localhost:8000/api/urls \
    -d '{"url":"https://example.com/flights"}' -H "Content-Type: application/json"
  # Duplicate — expect HTTP 409
  curl -X POST http://localhost:8000/api/urls \
    -d '{"url":"https://example.com/flights"}' -H "Content-Type: application/json"
  ```

---

### 02-02 — Unit tests for URL management `[done]`

- **Depends on**: 02-01
- **Files to create**: `backend/tests/test_urls.py`
- **Test cases**:
  1. Register valid URL → 201
  2. Register duplicate URL → 409
  3. Register invalid URL (no scheme) → 422
  4. Delete existing URL → 204
  5. Delete non-existent URL → 404
- **Verification**: `cd backend && pytest tests/test_urls.py -v` — all 5 tests pass

---

## Phase 3 — Scanner Service

### 03-01 — Implement ScannerAdapter abstract base class `[done]`

- **Depends on**: 01-03
- **Design ref**: Section 10.1 (Adapter Interface Definition — ScannerAdapter), NFR-05
- **NFR**: NFR-05 (Maintainability — scoring engine replaceability)
- **Files to create**:
  - `backend/app/services/scanner/base.py` — `AuditRecord` dataclass + `ScoreRecord` dataclass (with `audits: List[AuditRecord]` field) + `ScannerAdapter` ABC
- **Acceptance Criteria**: `from app.services.scanner.base import ScannerAdapter, AuditRecord, ScoreRecord` imports without error; instantiating `ScannerAdapter()` raises `TypeError`
- **Verification**: `python -c "from app.services.scanner.base import ScannerAdapter; ScannerAdapter()"`

---

### 03-02 — Implement LighthouseAdapter (PageSpeed Insights API) `[done]`

- **Depends on**: 03-01
- **Design ref**: Section 3 (LighthouseAdapter), Section 4.1 (Manual Scan flow), Section 10.1
- **FR**: FR-02, FR-03, FR-08 (per-audit detail emission)
- **Files to create**:
  - `backend/app/services/scanner/lighthouse.py` — `LighthouseAdapter(ScannerAdapter)`: calls `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}&strategy=mobile`; maps response JSON to `ScoreRecord` **and** to a list of `AuditRecord`
- **Score mapping**:
  - `performance_score` ← `lighthouseResult.categories.performance.score * 100`
  - `seo_score` ← `lighthouseResult.categories.seo.score * 100`
  - `accessibility_score` ← `lighthouseResult.categories.accessibility.score * 100`
  - `best_practices_score` ← `lighthouseResult.categories.best-practices.score * 100`
  - `lcp_ms` ← `lighthouseResult.audits.largest-contentful-paint.numericValue`
  - `inp_ms` ← `lighthouseResult.audits.interaction-to-next-paint.numericValue`
  - `cls` ← `lighthouseResult.audits.cumulative-layout-shift.numericValue`
  - Any missing field → `null`
- **Audit mapping** (FR-08 evidence):
  - For each `audit_id` referenced in any `lighthouseResult.categories[*].auditRefs`, emit `AuditRecord(audit_id, title, category, score, display_value)`
  - `category` = parent category name (`performance`, `seo`, `accessibility`, `best-practices`)
- **Acceptance Criteria**: `LighthouseAdapter().fetch_scores("https://example.com")` returns a `ScoreRecord` with the 7 score fields populated and `len(score_record.audits) > 0`
- **Verification**: Run with a real API key in `.env`; assert `len(result.audits) > 0` and each audit has `audit_id` + `category`

---

### 03-03 — Unit tests for LighthouseAdapter `[done]`

- **Depends on**: 03-02
- **Files to create**: `backend/tests/test_scanner.py`
- **Test cases** (use `unittest.mock.patch` to mock HTTP call):
  1. Valid PSI response → all 7 score fields populated
  2. PSI response missing `inp` field → `inp_ms = null`
  3. PSI HTTP 429 (rate limit) → raises `ScannerError`
  4. PSI response with N failing audits → `score_record.audits` contains N items with correct `audit_id` and `category` (FR-08)
- **Verification**: `cd backend && pytest tests/test_scanner.py -v` — all 4 tests pass

---

## Phase 4 — Scan Runner & Job API

### 04-01 — Implement ScanRunner service `[todo]`

- **Depends on**: 03-02, 01-02
- **Design ref**: Section 3 (ScanRunner), Section 4.1 (Manual Scan flow), Section 5.1 (ScanJob State Machine), Section 5.2 (ScanResult State Machine)
- **FR**: FR-02, FR-06, FR-08 (audit persistence)
- **Files to create**:
  - `backend/app/services/scan_runner.py`
- **Logic**:
  1. `create_job(triggered_by)` → INSERT `scan_jobs` with `status=pending`; return `job_id`
  2. `execute(job_id)` → UPDATE `status=running`; for each `registered_url`:
     - call `LighthouseAdapter.fetch_scores(url)` with retry (max 3×, exponential backoff 1s → 2s → 4s)
     - INSERT `scan_results`
     - **INSERT one `lighthouse_audits` row per `AuditRecord` in `ScoreRecord.audits`, linked to the new `scan_results.id`** (FR-08)
     - on all retries exhausted set `status=failed`
  3. after all URLs: UPDATE `scan_jobs (status=completed, completed_at, success_count, failure_count)`
- **Acceptance Criteria**: After calling `execute()`, `scan_jobs.status = "completed"`, one `scan_results` row exists per registered URL, and `lighthouse_audits` rows exist for each successful scan
- **Verification**: `sqlite3 seo.db "SELECT (SELECT COUNT(*) FROM scan_results), (SELECT COUNT(*) FROM lighthouse_audits);"` — both counts > 0

---

### 04-02 — Implement Scan API endpoints `[todo]`

- **Depends on**: 04-01
- **Design ref**: Section 7 (Scan — FR-02, FR-06)
- **FR**: FR-02
- **Files to create**:
  - `backend/app/api/scan.py` — `POST /api/scan`, `GET /api/scan/jobs`, `GET /api/scan/jobs/{id}`
- **Logic**:
  - `POST /api/scan`: create job (async background task); return `{ job_id }` with HTTP 202
  - `GET /api/scan/jobs/{id}`: return job status + `success_count`, `failure_count`
- **AC ref**: AC-03 (On-Demand Scan Execution)
- **Verification**:

  ```bash
  JOB=$(curl -s -X POST http://localhost:8000/api/scan | jq -r '.job_id')
  # Poll until completed
  curl http://localhost:8000/api/scan/jobs/$JOB
  ```

---

### 04-03 — Integration tests for scan flow `[todo]`

- **Depends on**: 04-02
- **Files to create**: `backend/tests/test_scan.py`
- **Test cases** (mock `LighthouseAdapter.fetch_scores`):
  1. POST /api/scan → 202 + job_id returned
  2. After job completes → scan_jobs.status == "completed"
  3. scan_results rows created for each registered URL
  4. **lighthouse_audits rows persisted with the expected audit_id values** (FR-08)
  5. Failed URL (mocked error) → retry_count == 3, scan_results.status == "failed"
- **Verification**: `cd backend && pytest tests/test_scan.py -v`

---

## Phase 5 — Scheduler

### 05-01 — Integrate APScheduler with FastAPI `[todo]`

- **Depends on**: 04-01
- **Design ref**: Section 3 (APScheduler), Section 4.2 (Scheduled Scan flow)
- **FR**: FR-06
- **Files to create**:
  - `backend/app/core/scheduler.py` — `AsyncIOScheduler`; `add_cron_job(scan_runner.run_scheduled_scan, hour, minute)`; starts on app startup; stops on shutdown
- **Acceptance Criteria**: On startup, APScheduler logs `"Job added: run_scheduled_scan"`; the job fires at the configured time
- **Verification**: Set `scan_time_utc = "HH:MM"` 2 minutes ahead; wait; check `scan_jobs` table for a new `triggered_by="scheduled"` row

---

### 05-02 — Implement Settings API endpoints `[todo]`

- **Depends on**: 05-01, 01-02
- **Design ref**: Section 7 (Settings — FR-06)
- **FR**: FR-06
- **Files to create**:
  - `backend/app/api/settings.py` — `GET /api/settings`, `PUT /api/settings`
- **Logic**: `PUT /api/settings` must update the singleton `app_settings` row (id=1); reschedule APScheduler job with new `hour` and `minute`
- **Acceptance Criteria**: After `PUT /api/settings` with new `scan_time_utc`, APScheduler job is rescheduled; subsequent `GET /api/settings` returns the updated values
- **Verification**: `curl -X PUT http://localhost:8000/api/settings -d '{"scan_frequency":"daily","scan_time_utc":"02:30","admin_email":"test@example.com"}' -H "Content-Type: application/json"`

---

## Phase 6 — Results API

### 06-01 — Implement GET /api/results/latest `[todo]`

- **Depends on**: 04-02, 01-03
- **Design ref**: Section 7 (Results), Section 4.3 (Dashboard Load flow)
- **FR**: FR-04
- **Files to create**: (add to `backend/app/api/results.py`)
- **SQL logic**: `SELECT DISTINCT ON (url_id) * FROM scan_results WHERE status='success' ORDER BY url_id, scanned_at DESC`
- **AC ref**: AC-05 (Dashboard Score Display)
- **Verification**: `curl http://localhost:8000/api/results/latest` returns one object per registered URL

---

### 06-02 — Implement GET /api/results/history `[todo]`

- **Depends on**: 06-01
- **Design ref**: Section 7 (Results), FR-05
- **FR**: FR-05
- **Logic**: Filter `scan_results` by `url_id`, `scanned_at >= from`, `scanned_at <= to`; return ordered by `scanned_at ASC`
- **AC ref**: AC-06 (Historical Trend View)
- **Verification**: `curl "http://localhost:8000/api/results/history?url_id=1&from=2026-04-01&to=2026-05-17"`

---

### 06-03 — Implement GET /api/results/compare `[todo]`

- **Depends on**: 06-01
- **Design ref**: Section 7 (Results), Section 4.5 (Score Comparison flow)
- **FR**: FR-07
- **Logic**: Fetch one record for `baseline` date and one for `comparison` date for the given `url_id`; if either is missing return HTTP 404 with `"No scan record found for the selected date"`; compute `delta = compare_score - baseline_score` per dimension
- **AC ref**: AC-08, AC-09
- **Verification**:

  ```bash
  curl "http://localhost:8000/api/results/compare?url_id=1&baseline=2026-04-01&comparison=2026-05-01"
  # Missing date test — expect HTTP 404
  curl "http://localhost:8000/api/results/compare?url_id=1&baseline=2026-03-15&comparison=2026-05-01"
  ```

---

### 06-04 — Implement GET /api/results/export (CSV) `[todo]`

- **Depends on**: 06-02
- **Design ref**: Section 7 (Results), FR-05
- **FR**: FR-05
- **Logic**: Same filter as `/history`; stream response as `text/csv` with headers: `url,scanned_at,performance_score,seo_score,accessibility_score,best_practices_score,lcp_ms,inp_ms,cls`
- **AC ref**: AC-06 (Export CSV)
- **Verification**: `curl "http://localhost:8000/api/results/export?url_id=1&from=2026-04-01&to=2026-05-17" -o export.csv && head export.csv`

---

### 06-05 — Integration tests for Results API `[todo]`

- **Depends on**: 06-01 ~ 06-04
- **Files to create**: `backend/tests/test_results.py`
- **Test cases**:
  1. `/latest` returns one result per registered URL
  2. `/history` returns results filtered by date range
  3. `/compare` with valid dates returns delta per dimension
  4. `/compare` with missing date returns HTTP 404
  5. `/export` returns valid CSV with correct column headers
- **Verification**: `cd backend && pytest tests/test_results.py -v`

---

## Phase 7 — Suggester Service & API (FR-08 Backend)

> **Priority note**: Higher priority than the Email Notifier (Phase 16). Implemented immediately after the Results API so the SEO-specialist persona can derive value as early as possible.

### 07-01 — Implement SuggesterAdapter abstract base class `[todo]`

- **Depends on**: 01-03, 03-01
- **Design ref**: Section 10.2 (Adapter Interface Definition — SuggesterAdapter), NFR-05, NFR-08
- **NFR**: NFR-05 (replaceability), NFR-08 (explainability)
- **Files to create**:
  - `backend/app/services/suggester/base.py` — `SuggestionRecord` dataclass + `SuggesterAdapter` ABC with `generate(url_id, latest_audits, history) → List[SuggestionRecord]`
- **Acceptance Criteria**: `from app.services.suggester.base import SuggesterAdapter, SuggestionRecord` imports without error; instantiating `SuggesterAdapter()` raises `TypeError`
- **Verification**: `python -c "from app.services.suggester.base import SuggesterAdapter; SuggesterAdapter()"`

---

### 07-02 — Implement HeuristicSuggester + audit templates `[todo]`

- **Depends on**: 07-01, 01-02 (`lighthouse_audit`, `suggestion` ORM models)
- **Design ref**: Section 3 (HeuristicSuggester), Section 6 (Confidence Rule), Section 10.2
- **FR**: FR-08
- **Files to create**:
  - `backend/app/services/suggester/templates.py` — static map `AUDIT_TEMPLATES: Dict[str, Tuple[str, str]]` mapping `audit_id → (affected_dimension, action_description)` for at least 15 common Lighthouse audits (e.g., `image-alt`, `meta-description`, `offscreen-images`, `unused-javascript`, `render-blocking-resources`, `uses-text-compression`, `largest-contentful-paint`, etc.)
  - `backend/app/services/suggester/heuristic.py` — `HeuristicSuggester(SuggesterAdapter)`
- **Logic**:
  1. Iterate `latest_audits`; keep only items with `score < 0.9`
  2. For each kept audit, lookup template by `audit_id`; **drop if no template exists** (FR-08 traceability constraint)
  3. Compute `estimated_impact`: mean Δ of the same `audit_id` across `history` (between prior scans where the audit went from failing → passing); `None` if `sample_size == 0`
  4. Assign `confidence_level` per Section 6 rule: `high` if sample_size ≥ 5; `medium` if 2–4; `low` if ≤ 1
  5. Return `List[SuggestionRecord]` sorted by descending `estimated_impact` (`None` sorts last)
- **Acceptance Criteria**: Given a fixture of failing audits + empty history, returns suggestions for templated audits with `confidence == "low"` and `estimated_impact == None`; given history with prior remediations, computes correct mean Δ and confidence
- **Verification**: `cd backend && pytest tests/test_suggester_heuristic.py -v`

---

### 07-03 — Implement SuggestionService + API endpoints `[todo]`

- **Depends on**: 07-02, 04-01 (`lighthouse_audits` exist in DB)
- **Design ref**: Section 3 (SuggestionService), Section 4.4 (Suggestion Generation flow), Section 7 (Suggestions API)
- **FR**: FR-08
- **NFR**: NFR-07 (suggestion latency < 5s), NFR-08 (traceability)
- **Files to create**:
  - `backend/app/services/suggester/service.py` — `SuggestionService`: orchestrates the `SuggesterAdapter` call, applies ranking, UPSERTs cached results into `improvement_suggestions` keyed by `(url_id, scan_result_id)`
  - `backend/app/api/suggestions.py` — `GET /api/suggestions?url_id={id}`, `GET /api/suggestions/audits?url_id={id}&scan_id={id?}`
- **Logic**:
  - On `GET /api/suggestions`: fetch latest `scan_result` + its `lighthouse_audits`; fetch history; call `SuggestionService.get_suggestions(url_id)`; return cached result if `(url_id, latest scan_result_id)` already exists in `improvement_suggestions`, else compute, cache, return
  - On `GET /api/suggestions/audits`: return raw `lighthouse_audits` for NFR-08 audit traceability
- **AC ref**: AC-10
- **Verification**:

  ```bash
  curl "http://localhost:8000/api/suggestions?url_id=1"
  # Confirm ranked array, first item has highest estimated_impact
  curl "http://localhost:8000/api/suggestions/audits?url_id=1"
  ```

---

### 07-04 — Integration tests for Suggester `[todo]`

- **Depends on**: 07-03
- **Files to create**: `backend/tests/test_suggestions.py`
- **Test cases**:
  1. AC-10: latest scan with N failing templated audits → `GET /api/suggestions` returns N ranked items within 5s (NFR-07)
  2. AC-11: failing audit with no historical precedent → returned item has `confidence_level == "low"` and `estimated_impact is None`
  3. Items returned are sorted by descending `estimated_impact` (with `None` last)
  4. Audits without a template entry are dropped from the response (FR-08 traceability constraint)
  5. Second call with no new scan returns the cached row (no recomputation) — assert `generated_at` is unchanged
- **Verification**: `cd backend && pytest tests/test_suggestions.py -v`

---

## Phase 8 — Frontend Foundation

### 08-01 — Configure Axios API client `[todo]`

- **Depends on**: 00-02
- **Design ref**: Section 8 (Directory Structure — `frontend/src/api/client.ts`)
- **Files to create**:
  - `frontend/src/api/client.ts` — Axios instance with `baseURL=http://localhost:8000`; response interceptor that surfaces error messages from the API response body
- **Acceptance Criteria**: Importing `client` in a page component does not throw; `client.get('/api/urls')` reaches the backend
- **Verification**: Browser DevTools → Network tab shows requests hitting `localhost:8000`

---

### 08-02 — Configure React Router `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.1 (Page Map)
- **Files to create**:
  - `frontend/src/main.tsx` — `<BrowserRouter>` wrapping `<App />`
  - `frontend/src/App.tsx` — routes: `/`, `/urls`, `/history`, `/compare`, `/suggestions`, `/settings`
- **Acceptance Criteria**: Navigating to `/` renders the Dashboard placeholder; each route — including `/suggestions` — renders its placeholder page without errors
- **Verification**: Manual browser test — navigate to each of the 6 routes directly

---

## Phase 9 — Frontend: Layout

### 09-01 — Implement Navbar component `[todo]`

- **Depends on**: 08-02
- **Files to create**:
  - `frontend/src/components/Navbar.tsx` — navigation links: Dashboard `/`, URL Manager `/urls`, History `/history`, Compare `/compare`, Suggestions `/suggestions`, Settings `/settings`
- **Acceptance Criteria**: Navbar renders on all pages; clicking each of the 6 links navigates to the correct route
- **Verification**: Manual browser test — click each nav link and confirm correct page renders

---

## Phase 10 — Frontend: Dashboard

### 10-01 — Implement StatusBadge component `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.2 (Dashboard Page)
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/components/StatusBadge.tsx` — props: `score: number | null`; renders 🟢 / 🟡 / 🔴 based on thresholds (≥90 / 50–89 / <50)
- **Verification**: Storybook or manual render with `score=92` (🟢), `score=65` (🟡), `score=40` (🔴)

---

### 10-02 — Implement ScoreTable component `[todo]`

- **Depends on**: 10-01
- **Design ref**: Section 9.2 (Dashboard Page)
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/components/ScoreTable.tsx` — props: `results: LatestResult[]`; renders table with columns: URL, Performance, SEO, A11y, Best Practices (each cell = `StatusBadge`), Last Scanned
- **Acceptance Criteria**: Table renders with correct badge colors per score value
- **Verification**: Manual render with mock data

---

### 10-03 — Implement Dashboard page `[todo]`

- **Depends on**: 10-02
- **Design ref**: Section 9.2
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/pages/Dashboard.tsx` — fetches `GET /api/results/latest` on mount; renders `<ScoreTable>`; "Scan Now" button calls `POST /api/scan` and polls `GET /api/scan/jobs/{id}` every 3s until `status=completed`; shows spinner during scan
- **AC ref**: AC-05 (Dashboard Score Display — loads within 3s, NFR-01)
- **Verification**: Open Dashboard → scores load; click "Scan Now" → spinner appears, then results refresh

---

## Phase 11 — Frontend: URL Manager

### 11-01 — Implement UrlManager page `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.1, FR-01
- **FR**: FR-01
- **Files to create**:
  - `frontend/src/pages/UrlManager.tsx` — lists registered URLs from `GET /api/urls`; form to register new URL (`POST /api/urls`); Delete button per row (`DELETE /api/urls/{id}`); shows inline validation error for duplicates (HTTP 409)
- **AC ref**: AC-01, AC-02
- **Verification**: Register URL → appears in list; register same URL → error message; delete URL → removed from list

---

## Phase 12 — Frontend: History

### 12-01 — Implement TrendChart component `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.3 (History Page)
- **FR**: FR-05
- **Files to create**:
  - `frontend/src/components/TrendChart.tsx` — props: `data: ScanResult[]`; renders Chart.js `<Line>` chart with 4 datasets (Performance, SEO, A11y, Best Practices); x-axis = `scanned_at` date; y-axis = 0–100
- **Verification**: Manual render with 30 days of mock data — chart renders with 4 lines

---

### 12-02 — Implement History page `[todo]`

- **Depends on**: 12-01
- **Design ref**: Section 9.3
- **FR**: FR-05
- **Files to create**:
  - `frontend/src/pages/History.tsx` — URL selector dropdown; date-range picker (`from` / `to`); on "Go" fetches `GET /api/results/history`; renders `<TrendChart>`; "Export CSV" button downloads `GET /api/results/export`
- **AC ref**: AC-06 (Historical Trend View + CSV Export)
- **Verification**: Select URL + 90-day range → chart renders; click "Export CSV" → file downloads with correct headers

---

## Phase 13 — Frontend: Compare

### 13-01 — Implement CompareTable component `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.4 (Compare Page)
- **FR**: FR-07
- **Files to create**:
  - `frontend/src/components/CompareTable.tsx` — props: `result: ComparisonResult`; renders table: Dimension | Baseline | Compare | Delta; delta column shows `▲ +{n}` (green) or `▼ -{n}` (red); CWV metrics (LCP, INP, CLS) use inverted color logic (lower = better → positive delta is green)
- **AC ref**: AC-08
- **Verification**: Manual render with mock deltas — confirm ▲ green / ▼ red and CWV inversion

---

### 13-02 — Implement Compare page `[todo]`

- **Depends on**: 13-01
- **Design ref**: Section 9.4
- **FR**: FR-07
- **Files to create**:
  - `frontend/src/pages/Compare.tsx` — URL selector; baseline date picker; comparison date picker; on "Go" fetches `GET /api/results/compare`; renders `<CompareTable>`; shows error message on HTTP 404
- **AC ref**: AC-08, AC-09
- **Verification**: Select URL + valid dates → delta table renders; select missing date → error displayed

---

## Phase 14 — Frontend: Suggestions (FR-08 Frontend)

> **Priority note**: It exposes the SEO-improvement-suggestion functionality introduced by FR-08 to the SEO Specialist persona.

### 14-01 — Implement SuggestionList component `[todo]`

- **Depends on**: 09-01, 07-03 (suggestion API available)
- **Design ref**: Section 9.5 (Suggestions Page), Section 7 (Suggestions API)
- **FR**: FR-08
- **Files to create**:
  - `frontend/src/components/SuggestionList.tsx` — props: `suggestions: SuggestionRecord[]`; renders one ranked row per suggestion with columns: Rank, Affected Dimension, Action Description, Δ Estimated Impact (or `N/A` when `estimated_impact == null`), Confidence (high / medium / low badge); each row is expandable to show the originating Lighthouse audit detail (`audit_id`, `title`, `display_value`) for NFR-08 traceability
- **Acceptance Criteria**: Renders ranked rows in input order; renders `"N/A"` for null impact; renders the audit_id evidence in the expanded view
- **Verification**: Manual render with mock data — confirm ranking + `N/A` rendering + audit_id visible on expand

---

### 14-02 — Implement Suggestions page `[todo]`

- **Depends on**: 14-01
- **Design ref**: Section 9.5, FR-08, NFR-07
- **FR**: FR-08
- **NFR**: NFR-07 (latency < 5s), NFR-08 (explainability)
- **Files to create**:
  - `frontend/src/pages/Suggestions.tsx` — URL selector dropdown (sourced from `GET /api/urls`); on selection fetches `GET /api/suggestions?url_id={id}` and renders `<SuggestionList>`; shows spinner during fetch; surfaces the `generated_at` timestamp from the response so the specialist can see whether the cache is stale
- **AC ref**: AC-10 (Suggestion Display), AC-11 (Confidence Fallback)
- **Verification**:
  - Select a URL with a recent scan that has failing audits → ranked list appears within 5s, top item has highest Δ
  - Select a URL whose failing audit has no historical precedent → its row shows `"low"` confidence and `"N/A"` impact

---

## Phase 15 — Frontend: Settings

### 15-01 — Implement Settings page `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.6 (Settings Page)
- **FR**: FR-06
- **Files to create**:
  - `frontend/src/pages/Settings.tsx` — fetches `GET /api/settings` on mount; form: frequency radio (`Daily`/`Weekly`), time input, admin email; on "Save" calls `PUT /api/settings`; shows success toast on 200
- **Acceptance Criteria**: Saving new `scan_time_utc` updates the scheduler; subsequent `GET /api/settings` returns updated values
- **Verification**: Change schedule to 2 minutes ahead; wait; confirm new scan job appears in `scan_jobs` table

---

## Phase 16 — Email Notifier

> **Priority note**: Deferred to after the Suggestions phase. Minimum code dependencies are Phase 0 (env vars) and Phase 4 (Scan Runner). No earlier phase is blocked by this phase. FR-08 (Suggestions) was prioritized ahead of FR-06's email notification because it directly serves the SEO Specialist persona's primary "Why".

### 16-01 — Implement Notifier service `[todo]`

- **Depends on**: 00-03, 04-01
- **Design ref**: Section 3 (Notifier), Section 4.1 (Manual Scan flow — email)
- **FR**: FR-06
- **Files to create**:
  - `backend/app/services/notifier.py` — `send_notification(job: ScanJob)`: builds plain-text email summarizing `success_count`, `failure_count`, `completed_at`; sends via `smtplib.SMTP` using env vars
- **Acceptance Criteria**: After a scan job completes, an email is delivered to `ADMIN_EMAIL` within 15 minutes
- **Verification**: Configure SMTP with a test mailbox (e.g., Mailtrap); trigger a scan; confirm email arrives

---

### 16-02 — Wire Notifier into ScanRunner `[todo]`

- **Depends on**: 16-01, 04-01
- **Files to modify**: `backend/app/services/scan_runner.py`
- **Change**: After `UPDATE scan_jobs (status=completed)`, call `notifier.send_notification(job)`
- **Acceptance Criteria**: End-to-end scan triggers email delivery
- **Verification**: Same as 16-01 — trigger scan via `POST /api/scan`; confirm email

---

## Phase 17 — Integration Testing & Polish

### 17-01 — End-to-end golden path test `[todo]`

- **Depends on**: All phases 00–16 done
- **Scenario**: Full user journey covering both the OTA-president and SEO-specialist personas
  1. Register 3 URLs via `POST /api/urls`
  2. Trigger manual scan via `POST /api/scan` → poll until `completed`
  3. Load Dashboard → verify scores visible within 3s (NFR-01)
  4. Load History page → verify chart renders for 1 URL
  5. Load Compare page → verify delta table renders
  6. **Load Suggestions page → verify ranked suggestions appear within 5s (NFR-07); verify each suggestion cites a Lighthouse audit ID (NFR-08)**
  7. Load Settings → change schedule; verify scheduler updates
  8. Trigger scan → verify email notification arrives
- **Verification**: Manually execute each step; record pass/fail per AC

---

### 17-02 — Performance check (NFR-01) `[todo]`

- **Depends on**: 10-03
- **NFR**: NFR-01 (Dashboard load < 3s)
- **Tool**: Chrome DevTools → Network tab → "DOMContentLoaded" and "Load" timings; or Lighthouse CLI on `http://localhost:5173/`
- **Acceptance Criteria**: Dashboard `Load` event fires in < 3000ms on a 50 Mbps throttled connection
- **Verification**: Chrome DevTools → Network tab → throttle to "Fast 4G"; reload Dashboard; confirm timing

---

### 17-03 — Performance check (NFR-07 — Suggestion latency) `[todo]`

- **Depends on**: 14-02
- **NFR**: NFR-07 (Suggestion generation latency < 5s per URL, server-side)
- **Tool**: `curl -w "%{time_total}\n"` or browser DevTools Network panel
- **Acceptance Criteria**: `GET /api/suggestions?url_id={id}` returns in < 5000ms on a URL with ≥ 10 failing audits and ≥ 30 days of history
- **Verification**:

  ```bash
  curl -o /dev/null -s -w "%{time_total}\n" "http://localhost:8000/api/suggestions?url_id=1"
  # Expect < 5.0
  ```

---

### 17-04 — Update README.md `[todo]`

- **Depends on**: All phases done
- **Files to modify**: `README.md`
- **Content**: Project overview, prerequisites, `docker-compose up` quick-start, environment variable table, link to `specs/` documents, **summary of the two supported personas (OTA President + SEO Specialist) and the features serving each**
- **Acceptance Criteria**: A developer unfamiliar with the project can run `docker-compose up` and access the dashboard + suggestions view after reading README
- **Verification**: Peer review of README clarity

---

## Summary Table

| Phase | Name | Steps | Key FR/NFR |
| --- | --- | --- | --- |
| 0 | Project Setup | 00-01 ~ 00-03 | — |
| 1 | DB & Models | 01-01 ~ 01-03 | All FRs + FR-08 |
| 2 | URL Management API | 02-01 ~ 02-02 | FR-01 |
| 3 | Scanner Service | 03-01 ~ 03-03 | FR-02, FR-03, FR-08, NFR-05 |
| 4 | Scan Runner & Job API | 04-01 ~ 04-03 | FR-02, FR-06, FR-08 |
| 5 | Scheduler | 05-01 ~ 05-02 | FR-06 |
| 6 | Results API | 06-01 ~ 06-05 | FR-04, FR-05, FR-07 |
| 7 | Suggester Service & API | 07-01 ~ 07-04 | FR-08, NFR-05, NFR-07, NFR-08 |
| 8 | Frontend Foundation | 08-01 ~ 08-02 | — |
| 9 | Layout | 09-01 | — |
| 10 | Dashboard | 10-01 ~ 10-03 | FR-04, NFR-01 |
| 11 | URL Manager | 11-01 | FR-01 |
| 12 | History | 12-01 ~ 12-02 | FR-05 |
| 13 | Compare | 13-01 ~ 13-02 | FR-07 |
| 14 | Suggestions (Frontend) | 14-01 ~ 14-02 | FR-08, NFR-07, NFR-08 |
| 15 | Settings | 15-01 | FR-06 |
| 16 | Email Notifier | 16-01 ~ 16-02 | FR-06 |
| 17 | Integration & Polish | 17-01 ~ 17-04 | NFR-01, NFR-07 |
| **Total** | | **45 steps** | |
