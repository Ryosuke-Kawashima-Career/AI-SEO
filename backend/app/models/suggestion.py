from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImprovementSuggestion(Base):
    __tablename__ = "improvement_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("registered_urls.id"), nullable=False
    )
    scan_result_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scan_results.id"), nullable=False
    )
    audit_id: Mapped[str] = mapped_column(String, nullable=False)
    affected_dimension: Mapped[str] = mapped_column(String, nullable=False)
    action_description: Mapped[str] = mapped_column(String, nullable=False)
    estimated_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
