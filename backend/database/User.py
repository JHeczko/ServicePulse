from typing import List

from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.core import Base


class User(Base):
    __tablename__ = 'users'

    # ==== STANDARD ATRIBUTES ====
    id: Mapped[int] = mapped_column(index=True, primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column(index=True)

    # ==== RELATIONSHIPS ====
    services: Mapped[List["Service"]] = relationship(back_populates="owner", cascade="all, delete-orphan")