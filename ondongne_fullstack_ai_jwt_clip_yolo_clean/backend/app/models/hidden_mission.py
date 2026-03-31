from sqlalchemy import Integer, String, Text, DateTime, func, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class HiddenMission(Base):
    __tablename__ = "hidden_missions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    week_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mission_type: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    bonus_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    predicted_overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    approve_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)
