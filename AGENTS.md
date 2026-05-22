# AI-SEO Agent Instructions

This file helps AI coding agents understand the `AI-SEO` repository quickly and work productively.

## Repository overview

- `backend/`: FastAPI-based Python service with SQLAlchemy models, Pydantic schemas, and APScheduler jobs.
- `frontend/`: React + Vite + TypeScript single-page application.
- `specs/`: spec-driven development documents. Changes to implementation should be aligned with `specs/implementation_plan.md`, `specs/design.md`, and `docs/walkthrough.md`.

## Primary focus areas

- Backend HTTP API and model layer: `backend/main.py`, `backend/app/api/urls.py`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/services/`.
- Lighthouse scanning and suggestion engine: `backend/app/services/scanner/`, `backend/app/models/suggestion.py`, `backend/app/models/scan_result.py`.
- Frontend dashboard and API integration: `frontend/src/`, especially `frontend/src/api/client.ts` and React components under `frontend/src/components/` and `frontend/src/pages/`.
- Tests: backend tests use `pytest` in `backend/tests/`.

## Build and run commands

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cp .env.example .env
docker compose up --build
```

## Helpful validation commands

- `curl http://localhost:8000/health`
- `curl http://localhost:8000/docs`
- `docker compose config`
- `cd backend && pytest`
- `cd frontend && npm run lint`

## Important conventions

- Preserve the repo's spec-driven workflow: use `specs/` and `docs/walkthrough.md` as the source of truth for feature scope and acceptance.
- Prefer minimal changes when adding new behavior; do not rewrite the whole app unless required.
- Keep backend and frontend responsibilities separate: backend exposes REST APIs, frontend consumes them via `frontend/src/api/client.ts`.
- `backend/app/api/urls.py` is the place where new backend routes should be registered.

## Documentation links

- Root README: `README.md`
- Specs: `specs/implementation_plan.md`, `specs/design.md`, `specs/requirements.md`, `specs/user_story.md`
- Walkthrough: `docs/walkthrough.md`
