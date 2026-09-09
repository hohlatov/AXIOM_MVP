"""
Личный кабинет / главный дашборд (базовая версия, п. 4.1 ТЗ).

Прогресс по предметам теперь берётся из последней завершённой диагностической
сессии (DiagnosticResult). Если диагностики ещё не было — прогресс 0%,
has_diagnostic_result=False. Рекомендации строятся по слабым темам из той же
диагностики. TODO: подмешать сюда статистику тренажёра (частые ошибки),
когда накопится достаточно данных.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.diagnostics import DiagnosticResult, DiagnosticSession
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, Recommendation, SubjectProgress

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SUBJECT_LABELS = {"math": "Математика", "russian": "Русский язык"}


async def _latest_completed_session(db: AsyncSession, user: User, subject: str) -> DiagnosticSession | None:
    return await db.scalar(
        select(DiagnosticSession)
        .where(DiagnosticSession.user_id == user.id, DiagnosticSession.subject == subject,
               DiagnosticSession.status == "completed")
        .order_by(DiagnosticSession.completed_at.desc())
        .limit(1)
    )


async def get_subject_progress(db: AsyncSession, user: User) -> tuple[list[SubjectProgress], bool]:
    progress = []
    has_any = False
    for code, label in SUBJECT_LABELS.items():
        session = await _latest_completed_session(db, user, code)
        if not session:
            progress.append(SubjectProgress(subject=code, subject_label=label, percent=0))
            continue
        has_any = True
        results = (
            await db.scalars(select(DiagnosticResult).where(DiagnosticResult.session_id == session.id))
        ).all()
        avg = int(round(100 * sum(r.ability_score for r in results) / len(results))) if results else 0
        progress.append(SubjectProgress(subject=code, subject_label=label, percent=avg))
    return progress, has_any


async def get_recommendations(db: AsyncSession, user: User) -> list[Recommendation]:
    recs = []
    for code in SUBJECT_LABELS:
        session = await _latest_completed_session(db, user, code)
        if not session:
            continue
        weak = (
            await db.scalars(
                select(DiagnosticResult).where(DiagnosticResult.session_id == session.id, DiagnosticResult.weak.is_(True))
            )
        ).all()
        for r in weak:
            recs.append(Recommendation(topic=r.topic, reason="Слабая тема по результатам диагностики"))
    return recs


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    progress, has_diagnostic_result = await get_subject_progress(db, user)
    recommendations = await get_recommendations(db, user)

    quick_actions = ["diagnostics", "trainer", "assistant"]

    return DashboardSummary(
        grade=user.grade,
        progress=progress,
        recommendations=recommendations,
        quick_actions=quick_actions,
        has_diagnostic_result=has_diagnostic_result,
    )
