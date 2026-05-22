import time
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.lighthouse_audit import LighthouseAudit
from app.models.scan_job import ScanJob
from app.models.scan_result import ScanResult
from app.models.url import RegisteredUrl
from app.services.scanner.base import ScannerAdapter, ScannerError, ScoreRecord
from app.services.scanner.lighthouse import LighthouseAdapter

# Backoffs applied BEFORE each retry attempt (initial attempt has none).
# 3 retries => 4 attempts total; full failure => retry_count == 3.
RETRY_BACKOFFS = (1.0, 2.0, 4.0)


def create_job(triggered_by: str, db: Session) -> int:
    job = ScanJob(triggered_by=triggered_by, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def execute(
    job_id: int, db: Session, adapter: ScannerAdapter | None = None
) -> None:
    adapter = adapter or LighthouseAdapter()
    job = db.get(ScanJob, job_id)
    if job is None:
        raise ValueError(f"No scan_jobs row for id={job_id}")

    urls = list(db.execute(select(RegisteredUrl)).scalars().all())
    job.status = "running"
    job.started_at = _utcnow()
    job.total_urls = len(urls)
    db.commit()

    success_count = 0
    failure_count = 0

    for url_row in urls:
        score, error_reason, retry_count = _fetch_with_retry(adapter, url_row.url)
        scanned_at = _utcnow()

        if score is not None:
            success_count += 1
            result = ScanResult(
                url_id=url_row.id,
                job_id=job_id,
                scanned_at=scanned_at,
                performance_score=score.performance_score,
                seo_score=score.seo_score,
                accessibility_score=score.accessibility_score,
                best_practices_score=score.best_practices_score,
                lcp_ms=score.lcp_ms,
                inp_ms=score.inp_ms,
                cls=score.cls,
                status="success",
                error_reason=None,
                retry_count=retry_count,
            )
            db.add(result)
            db.flush()  # need result.id before inserting audit rows
            for audit in score.audits:
                db.add(
                    LighthouseAudit(
                        scan_result_id=result.id,
                        audit_id=audit.audit_id,
                        title=audit.title,
                        category=audit.category,
                        score=audit.score,
                        display_value=audit.display_value,
                    )
                )
            db.commit()
        else:
            failure_count += 1
            db.add(
                ScanResult(
                    url_id=url_row.id,
                    job_id=job_id,
                    scanned_at=scanned_at,
                    performance_score=None,
                    seo_score=None,
                    accessibility_score=None,
                    best_practices_score=None,
                    lcp_ms=None,
                    inp_ms=None,
                    cls=None,
                    status="failed",
                    error_reason=error_reason,
                    retry_count=retry_count,
                )
            )
            db.commit()

    job = db.get(ScanJob, job_id)
    assert job is not None  # job_id was validated at the top of execute()
    job.status = "completed"
    job.completed_at = _utcnow()
    job.success_count = success_count
    job.failure_count = failure_count
    db.commit()


def _fetch_with_retry(
    adapter: ScannerAdapter, url: str
) -> tuple[ScoreRecord | None, str | None, int]:
    last_error: str | None = None
    try:
        return adapter.fetch_scores(url), None, 0
    except ScannerError as exc:
        last_error = str(exc)

    for retry_idx, backoff in enumerate(RETRY_BACKOFFS, start=1):
        time.sleep(backoff)
        try:
            return adapter.fetch_scores(url), None, retry_idx
        except ScannerError as exc:
            last_error = str(exc)

    return None, last_error, len(RETRY_BACKOFFS)


def run_scheduled_scan() -> None:
    """Entry point for APScheduler (Phase 5). Opens its own DB session."""
    db = SessionLocal()
    try:
        job_id = create_job("scheduled", db)
        execute(job_id, db)
    finally:
        db.close()
