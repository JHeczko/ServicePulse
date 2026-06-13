from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import Base


class Incident(Base):
    __tablename__ = "incidents"

    # ==== STANDARD ATRIBUTES ====
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(nullable=False)

    # ==== FK ====
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    # ==== RELATIONSHIP ====
    service: Mapped["Service"] = relationship("Service", back_populates="incidents")