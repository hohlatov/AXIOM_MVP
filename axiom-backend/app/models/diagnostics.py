import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="in_progress")  # in_progress | completed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("diagnostic_sessions.id"), index=True)
    topic: Mapped[str] = mapped_column(String(128))
    ability_score: Mapped[float] = mapped_column(Float)  # IRT-оценка, 0.0-1.0
    weak: Mapped[bool] = mapped_column(Boolean, default=False)


class DiagnosticAnswer(Base):
    """Сырые ответы ученика в рамках сессии — используются, чтобы передать
    историю ответов в ИИ-сервис при запросе следующего вопроса/финализации."""
    __tablename__ = "diagnostic_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("diagnostic_sessions.id"), index=True)
    item_id: Mapped[str] = mapped_column(String(64))
    answer: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
