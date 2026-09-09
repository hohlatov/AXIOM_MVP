import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TrainerTask(Base):
    __tablename__ = "trainer_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[str] = mapped_column(String(32))          # "math" | "russian"
    topic: Mapped[str] = mapped_column(String(128))            # напр. "Уравнения"
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)  # None => свободный ответ
    correct_answer: Mapped[str] = mapped_column(String(255))
    explanation: Mapped[str] = mapped_column(Text)  # разбор ошибки — показывается после ответа
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskAttempt(Base):
    __tablename__ = "task_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trainer_tasks.id"), index=True)
    submitted_answer: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
