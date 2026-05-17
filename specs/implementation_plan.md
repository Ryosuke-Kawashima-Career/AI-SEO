# Implementation Plan

> **Source**: [design.md](design.md)
> **Status**: Draft
> **Last Updated**: 2026-05-17

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
                                └── Phase 7 (Frontend Foundation)
                                      └── Phase 8 (Layout)
                                            ├── Phase 9  (Dashboard)
                                            ├── Phase 10 (URL Manager)
                                            ├── Phase 11 (History)
                                            ├── Phase 12 (Compare)
                                            └── Phase 13 (Settings)
                                                  └── Phase 14 (Email Notifier) *
                                                        └── Phase 15 (Integration & Polish)

* Phase 14 minimum code dependencies: Phase 0 (env vars) + Phase 4 (Scan Runner).
  Scheduled last among implementation phases due to lower business priority.
```

---

## Phase 0 — Project Setup & Infrastructure

### 00-01 — Initialize backend project structure `[todo]`

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
- **Acceptance Criteria**: `cd backend && python -m uvicorn main:app` starts without import errors
- **Verification**: `curl http://localhost:8000/docs` returns HTTP 200

---

### 00-02 — Initialize frontend project structure `[todo]`

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

### 00-03 — Create Docker & environment configuration `[todo]`

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

### 01-01 — Set up SQLAlchemy + SQLite connection `[todo]`

- **Depends on**: 00-01
- **Design ref**: Section 6 (Data Schema), Section 8
- **Files to create/modify**:
  - `backend/app/core/database.py` — engine, `SessionLocal`, `Base`, `get_db` dependency
- **Acceptance Criteria**: Importing `from app.core.database import Base` succeeds; `engine.connect()` creates `seo.db` file
- **Verification**: `python -c "from app.core.database import engine; engine.connect(); print('OK')"`

---

### 01-02 — Create ORM models `[todo]`

- **Depends on**: 01-01
- **Design ref**: Section 6 (ER Diagram)
- **Files to create**:
  - `backend/app/models/url.py` — `RegisteredUrl` (id, url UNIQUE, label, created_at, updated_at)
  - `backend/app/models/scan_job.py` — `ScanJob` (id, triggered_by, started_at, completed_at, total_urls, success_count, failure_count, status)
  - `backend/app/models/scan_result.py` — `ScanResult` (id, url_id FK, job_id FK, scanned_at, performance_score, seo_score, accessibility_score, best_practices_score, lcp_ms, inp_ms, cls, status, error_reason, retry_count)
  - `backend/app/models/settings.py` — `AppSettings` (id=1 singleton, scan_frequency, scan_time_utc, admin_email, updated_at)
- **Acceptance Criteria**: `Base.metadata.create_all(engine)` creates all 4 tables in `seo.db`
- **Verification**: `python -c "from app.core.database import Base, engine; from app.models import url, scan_job, scan_result, settings; Base.metadata.create_all(engine); print('Tables created')"` exits without error

---

### 01-03 — Create Pydantic schemas `[todo]`

- **Depends on**: 01-02
- **Design ref**: Section 7 (API Design — request/response bodies)
- **Files to create**:
  - `backend/app/schemas/url.py` — `UrlCreate`, `UrlResponse`
  - `backend/app/schemas/scan.py` — `ScanJobResponse`, `TriggerScanResponse`
  - `backend/app/schemas/result.py` — `ScanResultResponse`, `LatestResultResponse`, `ComparisonResultResponse`, `AppSettingsResponse`, `AppSettingsUpdate`
- **Acceptance Criteria**: All schema classes import without error; `UrlCreate(url="https://example.com")` instantiates correctly
- **Verification**: `python -c "from app.schemas.url import UrlCreate; print(UrlCreate(url='https://x.com'))"`

---

## Phase 2 — URL Management API

### 02-01 — Implement URL CRUD endpoints `[todo]`

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

### 02-02 — Unit tests for URL management `[todo]`

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

### 03-01 — Implement ScannerAdapter abstract base class `[todo]`

- **Depends on**: 01-03
- **Design ref**: Section 10 (Adapter Interface Definition), NFR-05
- **NFR**: NFR-05 (Maintainability — scoring engine replaceability)
- **Files to create**:
  - `backend/app/services/scanner/base.py` — `ScoreRecord` dataclass + `ScannerAdapter` ABC
- **Acceptance Criteria**: `from app.services.scanner.base import ScannerAdapter` imports without error; instantiating `ScannerAdapter()` raises `TypeError`
- **Verification**: `python -c "from app.services.scanner.base import ScannerAdapter; ScannerAdapter()"`

---

### 03-02 — Implement LighthouseAdapter (PageSpeed Insights API) `[todo]`

- **Depends on**: 03-01
- **Design ref**: Section 3 (LighthouseAdapter), Section 4.1 (Manual Scan flow)
- **FR**: FR-02, FR-03
- **Files to create**:
  - `backend/app/services/scanner/lighthouse.py` — `LighthouseAdapter(ScannerAdapter)`: calls `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}&strategy=mobile`; maps response JSON to `ScoreRecord`
- **Score mapping**:
  - `performance_score` ← `lighthouseResult.categories.performance.score * 100`
  - `seo_score` ← `lighthouseResult.categories.seo.score * 100`
  - `accessibility_score` ← `lighthouseResult.categories.accessibility.score * 100`
  - `best_practices_score` ← `lighthouseResult.categories.best-practices.score * 100`
  - `lcp_ms` ← `lighthouseResult.audits.largest-contentful-paint.numericValue`
  - `inp_ms` ← `lighthouseResult.audits.interaction-to-next-paint.numericValue`
  - `cls` ← `lighthouseResult.audits.cumulative-layout-shift.numericValue`
  - Any missing field → `null`
- **Acceptance Criteria**: `LighthouseAdapter().fetch_scores("https://example.com")` returns a `ScoreRecord` with all 7 fields (may be `null` for unavailable metrics)
- **Verification**: Run with a real API key in `.env`; assert response type is `ScoreRecord`

---

### 03-03 — Unit tests for LighthouseAdapter `[todo]`

- **Depends on**: 03-02
- **Files to create**: `backend/tests/test_scanner.py`
- **Test cases** (use `unittest.mock.patch` to mock HTTP call):
  1. Valid PSI response → all 7 fields populated
  2. PSI response missing `inp` field → `inp_ms = null`
  3. PSI HTTP 429 (rate limit) → raises `ScannerError`
- **Verification**: `cd backend && pytest tests/test_scanner.py -v` — all 3 tests pass

---

## Phase 4 — Scan Runner & Job API

### 04-01 — Implement ScanRunner service `[todo]`

- **Depends on**: 03-02, 01-02
- **Design ref**: Section 3 (ScanRunner), Section 4.1 (Manual Scan flow), Section 5.1 (ScanJob State Machine), Section 5.2 (ScanResult State Machine)
- **FR**: FR-02, FR-06
- **Files to create**:
  - `backend/app/services/scan_runner.py`
- **Logic**:
  1. `create_job(triggered_by)` → INSERT `scan_jobs` with `status=pending`; return `job_id`
  2. `execute(job_id)` → UPDATE `status=running`; for each `registered_url`: call `LighthouseAdapter.fetch_scores(url)` with retry (max 3×, exponential backoff 1s → 2s → 4s); INSERT `scan_results`; on all retries exhausted set `status=failed`; after all URLs: UPDATE `scan_jobs (status=completed, completed_at, success_count, failure_count)`
- **Acceptance Criteria**: After calling `execute()`, `scan_jobs.status = "completed"` and one `scan_results` row exists per registered URL
- **Verification**: Manual DB inspection with `sqlite3 seo.db "SELECT status FROM scan_jobs ORDER BY id DESC LIMIT 1;"`

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
  4. Failed URL (mocked error) → retry_count == 3, scan_results.status == "failed"
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
- **Design ref**: Section 7 (Results), Section 4.4 (Score Comparison flow)
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

## Phase 7 — Frontend Foundation

### 07-01 — Configure Axios API client `[todo]`

- **Depends on**: 00-02
- **Design ref**: Section 8 (Directory Structure — `frontend/src/api/client.ts`)
- **Files to create**:
  - `frontend/src/api/client.ts` — Axios instance with `baseURL=http://localhost:8000`; response interceptor that surfaces error messages from the API response body
- **Acceptance Criteria**: Importing `client` in a page component does not throw; `client.get('/api/urls')` reaches the backend
- **Verification**: Browser DevTools → Network tab shows requests hitting `localhost:8000`

---

### 07-02 — Configure React Router `[todo]`

- **Depends on**: 07-01
- **Design ref**: Section 9.1 (Page Map)
- **Files to create**:
  - `frontend/src/main.tsx` — `<BrowserRouter>` wrapping `<App />`
  - `frontend/src/App.tsx` — routes: `/`, `/urls`, `/history`, `/compare`, `/settings`
- **Acceptance Criteria**: Navigating to `/` renders the Dashboard placeholder; each route renders its placeholder page without errors
- **Verification**: Manual browser test — navigate to each route directly

---

## Phase 8 — Frontend: Layout

### 08-01 — Implement Navbar component `[todo]`

- **Depends on**: 07-02
- **Files to create**:
  - `frontend/src/components/Navbar.tsx` — navigation links: Dashboard `/`, URL Manager `/urls`, History `/history`, Compare `/compare`, Settings `/settings`
- **Acceptance Criteria**: Navbar renders on all pages; clicking each link navigates to the correct route
- **Verification**: Manual browser test — click each nav link and confirm correct page renders

---

## Phase 9 — Frontend: Dashboard

### 09-01 — Implement StatusBadge component `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.2 (Dashboard Page)
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/components/StatusBadge.tsx` — props: `score: number | null`; renders 🟢 / 🟡 / 🔴 based on thresholds (≥80 / 50–79 / <50)
- **Verification**: Storybook or manual render with `score=92` (🟢), `score=65` (🟡), `score=40` (🔴)

---

### 09-02 — Implement ScoreTable component `[todo]`

- **Depends on**: 09-01
- **Design ref**: Section 9.2 (Dashboard Page)
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/components/ScoreTable.tsx` — props: `results: LatestResult[]`; renders table with columns: URL, Performance, SEO, A11y, Best Practices (each cell = `StatusBadge`), Last Scanned
- **Acceptance Criteria**: Table renders with correct badge colors per score value
- **Verification**: Manual render with mock data

---

### 09-03 — Implement Dashboard page `[todo]`

- **Depends on**: 09-02
- **Design ref**: Section 9.2
- **FR**: FR-04
- **Files to create**:
  - `frontend/src/pages/Dashboard.tsx` — fetches `GET /api/results/latest` on mount; renders `<ScoreTable>`; "Scan Now" button calls `POST /api/scan` and polls `GET /api/scan/jobs/{id}` every 3s until `status=completed`; shows spinner during scan
- **AC ref**: AC-05 (Dashboard Score Display — loads within 3s, NFR-01)
- **Verification**: Open Dashboard → scores load; click "Scan Now" → spinner appears, then results refresh

---

## Phase 10 — Frontend: URL Manager

### 10-01 — Implement UrlManager page `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.1, FR-01
- **FR**: FR-01
- **Files to create**:
  - `frontend/src/pages/UrlManager.tsx` — lists registered URLs from `GET /api/urls`; form to register new URL (`POST /api/urls`); Delete button per row (`DELETE /api/urls/{id}`); shows inline validation error for duplicates (HTTP 409)
- **AC ref**: AC-01, AC-02
- **Verification**: Register URL → appears in list; register same URL → error message; delete URL → removed from list

---

## Phase 11 — Frontend: History

### 11-01 — Implement TrendChart component `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.3 (History Page)
- **FR**: FR-05
- **Files to create**:
  - `frontend/src/components/TrendChart.tsx` — props: `data: ScanResult[]`; renders Chart.js `<Line>` chart with 4 datasets (Performance, SEO, A11y, Best Practices); x-axis = `scanned_at` date; y-axis = 0–100
- **Verification**: Manual render with 30 days of mock data — chart renders with 4 lines

---

### 11-02 — Implement History page `[todo]`

- **Depends on**: 11-01
- **Design ref**: Section 9.3
- **FR**: FR-05
- **Files to create**:
  - `frontend/src/pages/History.tsx` — URL selector dropdown; date-range picker (`from` / `to`); on "Go" fetches `GET /api/results/history`; renders `<TrendChart>`; "Export CSV" button downloads `GET /api/results/export`
- **AC ref**: AC-06 (Historical Trend View + CSV Export)
- **Verification**: Select URL + 90-day range → chart renders; click "Export CSV" → file downloads with correct headers

---

## Phase 12 — Frontend: Compare

### 12-01 — Implement CompareTable component `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.4 (Compare Page)
- **FR**: FR-07
- **Files to create**:
  - `frontend/src/components/CompareTable.tsx` — props: `result: ComparisonResult`; renders table: Dimension | Baseline | Compare | Delta; delta column shows `▲ +{n}` (green) or `▼ -{n}` (red); CWV metrics (LCP, INP, CLS) use inverted color logic (lower = better → positive delta is green)
- **AC ref**: AC-08
- **Verification**: Manual render with mock deltas — confirm ▲ green / ▼ red and CWV inversion

---

### 12-02 — Implement Compare page `[todo]`

- **Depends on**: 12-01
- **Design ref**: Section 9.4
- **FR**: FR-07
- **Files to create**:
  - `frontend/src/pages/Compare.tsx` — URL selector; baseline date picker; comparison date picker; on "Go" fetches `GET /api/results/compare`; renders `<CompareTable>`; shows error message on HTTP 404
- **AC ref**: AC-08, AC-09
- **Verification**: Select URL + valid dates → delta table renders; select missing date → error displayed

---

## Phase 13 — Frontend: Settings

### 13-01 — Implement Settings page `[todo]`

- **Depends on**: 08-01
- **Design ref**: Section 9.5 (Settings Page)
- **FR**: FR-06
- **Files to create**:
  - `frontend/src/pages/Settings.tsx` — fetches `GET /api/settings` on mount; form: frequency radio (`Daily`/`Weekly`), time input, admin email; on "Save" calls `PUT /api/settings`; shows success toast on 200
- **Acceptance Criteria**: Saving new `scan_time_utc` updates the scheduler; subsequent `GET /api/settings` returns updated values
- **Verification**: Change schedule to 2 minutes ahead; wait; confirm new scan job appears in `scan_jobs` table

---

## Phase 14 — Email Notifier

> **Priority note**: Deferred to after all frontend phases. Minimum code dependencies are Phase 0 (env vars) and Phase 4 (Scan Runner). No earlier phase is blocked by this phase.

### 14-01 — Implement Notifier service `[todo]`

- **Depends on**: 00-03, 04-01
- **Design ref**: Section 3 (Notifier), Section 4.1 (Manual Scan flow — email)
- **FR**: FR-06
- **Files to create**:
  - `backend/app/services/notifier.py` — `send_notification(job: ScanJob)`: builds plain-text email summarizing `success_count`, `failure_count`, `completed_at`; sends via `smtplib.SMTP` using env vars
- **Acceptance Criteria**: After a scan job completes, an email is delivered to `ADMIN_EMAIL` within 15 minutes
- **Verification**: Configure SMTP with a test mailbox (e.g., Mailtrap); trigger a scan; confirm email arrives

---

### 14-02 — Wire Notifier into ScanRunner `[todo]`

- **Depends on**: 14-01, 04-01
- **Files to modify**: `backend/app/services/scan_runner.py`
- **Change**: After `UPDATE scan_jobs (status=completed)`, call `notifier.send_notification(job)`
- **Acceptance Criteria**: End-to-end scan triggers email delivery
- **Verification**: Same as 14-01 — trigger scan via `POST /api/scan`; confirm email

---

## Phase 15 — Integration Testing & Polish

### 15-01 — End-to-end golden path test `[todo]`

- **Depends on**: All phases 00–14 done
- **Scenario**: Full user journey from URL registration to comparison view
  1. Register 3 URLs via `POST /api/urls`
  2. Trigger manual scan via `POST /api/scan` → poll until `completed`
  3. Load Dashboard → verify scores visible within 3s (NFR-01)
  4. Load History page → verify chart renders for 1 URL
  5. Load Compare page → verify delta table renders
  6. Load Settings → change schedule; verify scheduler updates
  7. Trigger scan → verify email notification arrives
- **Verification**: Manually execute each step; record pass/fail per AC

---

### 15-02 — Performance check (NFR-01) `[todo]`

- **Depends on**: 09-03
- **NFR**: NFR-01 (Dashboard load < 3s)
- **Tool**: Chrome DevTools → Network tab → "DOMContentLoaded" and "Load" timings; or Lighthouse CLI on `http://localhost:5173/`
- **Acceptance Criteria**: Dashboard `Load` event fires in < 3000ms on a 50 Mbps throttled connection
- **Verification**: Chrome DevTools → Network tab → throttle to "Fast 4G"; reload Dashboard; confirm timing

---

### 15-03 — Update README.md `[todo]`

- **Depends on**: All phases done
- **Files to modify**: `README.md`
- **Content**: Project overview, prerequisites, `docker-compose up` quick-start, environment variable table, link to `specs/` documents
- **Acceptance Criteria**: A developer unfamiliar with the project can run `docker-compose up` and access the dashboard after reading README
- **Verification**: Peer review of README clarity

---

## Summary Table

| Phase | Name | Steps | Key FR/NFR |
| --- | --- | --- | --- |
| 0 | Project Setup | 00-01 ~ 00-03 | — |
| 1 | DB & Models | 01-01 ~ 01-03 | All FRs |
| 2 | URL Management API | 02-01 ~ 02-02 | FR-01 |
| 3 | Scanner Service | 03-01 ~ 03-03 | FR-02, FR-03, NFR-05 |
| 4 | Scan Runner & Job API | 04-01 ~ 04-03 | FR-02, FR-06 |
| 5 | Scheduler | 05-01 ~ 05-02 | FR-06 |
| 6 | Results API | 06-01 ~ 06-05 | FR-04, FR-05, FR-07 |
| 7 | Frontend Foundation | 07-01 ~ 07-02 | — |
| 8 | Layout | 08-01 | — |
| 9 | Dashboard | 09-01 ~ 09-03 | FR-04, NFR-01 |
| 10 | URL Manager | 10-01 | FR-01 |
| 11 | History | 11-01 ~ 11-02 | FR-05 |
| 12 | Compare | 12-01 ~ 12-02 | FR-07 |
| 13 | Settings | 13-01 | FR-06 |
| 14 | Email Notifier | 14-01 ~ 14-02 | FR-06 |
| 15 | Integration & Polish | 15-01 ~ 15-03 | NFR-01 |
| **Total** | | **38 steps** | |
