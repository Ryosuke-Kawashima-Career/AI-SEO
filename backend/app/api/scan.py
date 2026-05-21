from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.models.scan_job import ScanJob
from app.schemas.scan import ScanJobResponse, TriggerScanResponse
from app.services import scan_runner

router = APIRouter(prefix="/api/scan", tags=["scan"])


def _execute_in_background(job_id: int) -> None:
    db = SessionLocal()
    try:
        scan_runner.execute(job_id, db)
    finally:
        db.close()


@router.post(
    "",
    response_model=TriggerScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_scan(
    background: BackgroundTasks, db: Session = Depends(get_db)
) -> TriggerScanResponse:
    job_id = scan_runner.create_job("manual", db)
    background.add_task(_execute_in_background, job_id)
    return TriggerScanResponse(job_id=job_id)


@router.get("/jobs", response_model=list[ScanJobResponse])
def list_jobs(db: Session = Depends(get_db)) -> list[ScanJob]:
    return list(
        db.execute(select(ScanJob).order_by(ScanJob.id.desc())).scalars().all()
    )


@router.get("/jobs/{job_id}", response_model=ScanJobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> ScanJob:
    job = db.get(ScanJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found"
        )
    return job
