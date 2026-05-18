from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    title: str
    category: str
    score: float | None
    display_value: str | None


class SuggestionEvidence(BaseModel):
    sample_size: int
    historical_scan_ids: list[int]


class SuggestionRecord(BaseModel):
    audit_id: str
    affected_dimension: str
    action_description: str
    estimated_impact: float | None
    confidence_level: str
    rank: int
    evidence: SuggestionEvidence


class SuggestionResponse(BaseModel):
    url_id: int
    scan_id: int
    generated_at: datetime
    suggestions: list[SuggestionRecord]
