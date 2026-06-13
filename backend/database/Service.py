from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from backend.database import User
from backend.database.core import Base

class Service(Base):
    __tablename__ = 'services'

    # ==== STANDARD ATRIBUTES ====
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    # interval in seconds
    interval: Mapped[int] = mapped_column(nullable=False)

    # ==== FK ====
    user_id: Mapped[int] = mapped_column( ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE") ,nullable=False)

    # ==== RELATIONSHIPS ====
    owner: Mapped[User] = relationship(back_populates="services")