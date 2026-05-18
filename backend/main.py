from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import urls
from app.core.database import Base, engine
from app.models import (
    lighthouse_audit,
    scan_job,
    scan_result,
    settings,
    suggestion,
    url,
)

# Force model registration with Base.metadata before create_all.
_REGISTERED_MODELS = (
    url,
    scan_job,
    scan_result,
    lighthouse_audit,
    suggestion,
    settings,
)

Base.metadata.create_all(engine)

app = FastAPI(title="AI-SEO Evaluation System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(urls.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
