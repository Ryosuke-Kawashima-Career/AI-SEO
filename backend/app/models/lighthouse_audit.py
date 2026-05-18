from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LighthouseAudit(Base):
    __tablename__ = "lighthouse_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_result_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scan_results.id"), nullable=False
    )
    audit_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_value: Mapped[str | None] = mapped_column(String, nullable=True)
