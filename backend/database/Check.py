from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class Check(Base):
    __tablename__ = "checks"

    # ==== STANDARD ATRIBUTES ====
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status_code: Mapped[int] = mapped_column(nullable=False)
    response_time_ms: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    # ==== FK ====
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        Index("ix_checks_service_time", "service_id", "created_at"),
    )