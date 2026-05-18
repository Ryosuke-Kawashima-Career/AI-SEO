from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("registered_urls.id"), nullable=False
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scan_jobs.id"), nullable=False
    )
    scanned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    seo_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accessibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_practices_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lcp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    inp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cls: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
