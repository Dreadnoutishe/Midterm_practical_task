from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class WantedCriminal(Base):
    __tablename__ = "wanted_criminals"
    __table_args__ = (
        CheckConstraint("reward >= 0", name="nonnegative_reward"),
        CheckConstraint("difficulty BETWEEN 1 AND 10", name="valid_difficulty"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nickname: Mapped[str] = mapped_column(String(120))
    reward: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    last_known_location: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int]
    armed: Mapped[bool] = mapped_column(Boolean)
    has_crew: Mapped[bool] = mapped_column(Boolean)
    escape_master: Mapped[bool] = mapped_column(Boolean)
    hunt_logs: Mapped[list["HuntLog"]] = relationship(back_populates="criminal")

class HuntLog(Base):
    __tablename__ = "hunt_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("wanted_criminals.id"), index=True)
    success: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    criminal: Mapped[WantedCriminal] = relationship(back_populates="hunt_logs")
