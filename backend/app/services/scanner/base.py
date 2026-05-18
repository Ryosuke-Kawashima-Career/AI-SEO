from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ScannerError(Exception):
    """Raised when a scoring engine call fails unrecoverably."""


@dataclass
class AuditRecord:
    audit_id: str
    title: str
    category: str
    score: float | None
    display_value: str | None


@dataclass
class ScoreRecord:
    performance_score: float | None
    seo_score: float | None
    accessibility_score: float | None
    best_practices_score: float | None
    lcp_ms: float | None
    inp_ms: float | None
    cls: float | None
    audits: list[AuditRecord] = field(default_factory=list)


class ScannerAdapter(ABC):
    @abstractmethod
    def fetch_scores(self, url: str) -> ScoreRecord:
        """Fetch SEO scores and per-audit detail for the given URL."""
