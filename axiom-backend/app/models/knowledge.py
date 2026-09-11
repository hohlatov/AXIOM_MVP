import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class KnowledgeState(Base):
    """Живая карта навыков ученика (killer feature, см. docs/product/04-killer-feature.md
    и docs/architecture/adaptive-learning-engine.md) — детерминированная EWMA-оценка
    владения темой, обновляемая после каждой попытки в тренажёре. Не ML, не CAT/IRT —
    осознанно простая формула на MVP (CLAUDE.md, принцип 5).

    Ключ — (user_id, subject, topic) строкой, а не нормализованный topic_id: полноценный
    справочник тем — задача Launch-стадии (см. docs/architecture/03-database-design-v2.md),
    сейчас это излишняя сложность для одной таблицы."""
    __tablename__ = "knowledge_state"
    __table_args__ = (UniqueConstraint("user_id", "subject", "topic", name="uq_knowledge_state_user_subject_topic"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(32))
    topic: Mapped[str] = mapped_column(String(128))
    ability_score: Mapped[float] = mapped_column(Float)  # EWMA, 0.0-1.0
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
