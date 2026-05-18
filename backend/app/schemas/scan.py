from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScanJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    triggered_by: str
    started_at: datetime | None
    completed_at: datetime | None
    total_urls: int
    success_count: int
    failure_count: int
    status: str


class TriggerScanResponse(BaseModel):
    job_id: int
