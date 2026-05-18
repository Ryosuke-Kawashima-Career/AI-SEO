# AI-SEO

An automated SEO Evaluation System for an OTA (Online Travel Agency). It uses **Lighthouse** (via the Google PageSpeed Insights API) to score registered pages on a recurring schedule, surfaces the scores on a dashboard, tracks them historically, and produces ranked SEO improvement suggestions for the SEO specialist.

See [specs/](specs/) for the full requirements, design, and implementation plan.

---

## Repository Layout

```text
AI-SEO/
├── backend/          # FastAPI + SQLAlchemy + APScheduler (Python 3.12+)
├── frontend/         # React + Vite + TypeScript
├── specs/            # SDD documents (requirements / design / plan)
├── docker-compose.yml
└── .env.example
```

---

## Prerequisites

| Tool | Tested version | Notes |
|---|---|---|
| **Python** | 3.12 or newer (validated on 3.13) | Required for backend |
| **Node.js** | 20 or newer (validated on 25) | Required for frontend |
| **Docker** | 24+ (optional) | Only if you use `docker compose` |

---

## Running locally (without Docker)

### 1. Set environment variables

```bash
cp .env.example .env
# Optional: edit .env to add your PAGESPEED_API_KEY and SMTP credentials.
# These are NOT required to start the servers in Phase 0.
```

### 2. Start the backend (FastAPI on port 8000)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Verify in another terminal:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs    # expect 200
curl     http://localhost:8000/health                                  # expect {"status":"ok"}
```

The auto-generated OpenAPI docs are live at <http://localhost:8000/docs>.

### 3. Start the frontend (Vite on port 5173)

```bash
cd frontend
npm install
npm run dev
```

Verify in a browser at <http://localhost:5173/> — the Vite + React splash page should render.

---

## Running with Docker

Set up your docker desktop first.

```bash
cp .env.example .env
docker compose up --build
```

- Backend: <http://localhost:8000/docs>
- Frontend: <http://localhost:5173/>

Stop the stack with `Ctrl+C`, then `docker compose down`.

---

## Smoke-test summary (Phase 0)

| Step | What you verify | Expected |
|---|---|---|
| 00-01 | `curl http://localhost:8000/docs` | HTTP 200 |
| 00-01 | `curl http://localhost:8000/health` | `{"status":"ok"}` |
| 00-02 | Open <http://localhost:5173/> in a browser | Vite + React splash page renders |
| 00-03 | `docker compose config` | Exits with status 0 (config valid) |

---

## Project Status

Phase 0 (Project Setup & Infrastructure) is complete. The backend exposes `/health` and `/docs`; the frontend Vite scaffold runs. Subsequent phases will add URL management, the Lighthouse scanner, the suggestion engine, and the React dashboard — see [specs/implementation_plan.md](specs/implementation_plan.md).
