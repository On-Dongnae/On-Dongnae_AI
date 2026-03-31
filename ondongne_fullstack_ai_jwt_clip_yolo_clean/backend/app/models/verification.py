from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class ActivityVerification(Base):
    __tablename__ = "activity_verifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mission_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_probabilities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_raw_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="verifications")
    images = relationship("VerificationImage", back_populates="verification", cascade="all, delete-orphan")

class VerificationImage(Base):
    __tablename__ = "verification_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("activity_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    verification = relationship("ActivityVerification", back_populates="images")
