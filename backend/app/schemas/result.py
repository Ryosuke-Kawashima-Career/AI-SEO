from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url_id: int
    job_id: int
    scanned_at: datetime
    performance_score: float | None
    seo_score: float | None
    accessibility_score: float | None
    best_practices_score: float | None
    lcp_ms: float | None
    inp_ms: float | None
    cls: float | None
    status: str


class LatestResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url_id: int
    url: str
    scanned_at: datetime
    performance_score: float | None
    seo_score: float | None
    accessibility_score: float | None
    best_practices_score: float | None
    lcp_ms: float | None
    inp_ms: float | None
    cls: float | None


class DimensionDelta(BaseModel):
    baseline: float | None
    comparison: float | None
    delta: float | None


class ComparisonResultResponse(BaseModel):
    url_id: int
    baseline_date: str
    comparison_date: str
    performance: DimensionDelta
    seo: DimensionDelta
    accessibility: DimensionDelta
    best_practices: DimensionDelta
    lcp: DimensionDelta
    inp: DimensionDelta
    cls: DimensionDelta


class AppSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_frequency: str
    scan_time_utc: str
    admin_email: str | None
    updated_at: datetime


class AppSettingsUpdate(BaseModel):
    scan_frequency: str
    scan_time_utc: str
    admin_email: str | None = None
