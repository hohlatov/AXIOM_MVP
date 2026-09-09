"""
Диагностика (CAT/IRT) — обвязка вокруг ИИ-сервиса Валентины (п. 4.2 ТЗ).

Backend отвечает за сессии и хранение результатов; сама генерация вопросов
и IRT-логика — у ИИ-сервиса (docs/ai-service-contract.md). Пока её сервис не
задеплоен, работаем в mock-режиме (AI_SERVICE_MOCK=true) — см. app/core/ai_client.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.ai_client import AIServiceError, finalize_session, get_next_item
from app.db.session import get_db
from app.models.diagnostics import DiagnosticAnswer, DiagnosticResult, DiagnosticSession
from app.models.user import User
from app.schemas.diagnostics import (
    AnswerIn,
    DiagnosticItem,
    DiagnosticResultOut,
    StartDiagnosticOut,
    TopicResult,
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.post("/start", response_model=StartDiagnosticOut, status_code=status.HTTP_201_CREATED)
async def start_diagnostic(
    subject: str = Query(pattern="^(math|russian)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = DiagnosticSession(user_id=user.id, subject=subject, status="in_progress")
    db.add(session)
    await db.commit()
    await db.refresh(session)

    try:
        item = await get_next_item(str(session.id), subject, previous_answers=[])
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return StartDiagnosticOut(session_id=session.id, item=DiagnosticItem(**item))


@router.post("/answer", response_model=StartDiagnosticOut)
async def submit_diagnostic_answer(
    payload: AnswerIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(DiagnosticSession, payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
    if session.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Сессия уже завершена")

    answer = DiagnosticAnswer(session_id=session.id, item_id=payload.item_id, answer=payload.answer)
    db.add(answer)
    await db.commit()

    history = await _get_answers(db, session.id)

    try:
        item = await get_next_item(str(session.id), session.subject, previous_answers=history)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return StartDiagnosticOut(session_id=session.id, item=DiagnosticItem(**item))


@router.post("/{session_id}/finalize", response_model=DiagnosticResultOut)
async def finalize_diagnostic(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(DiagnosticSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
    if session.status == "completed":
        return await _load_result(db, session)

    history = await _get_answers(db, session.id)
    try:
        topics = await finalize_session(str(session.id), session.subject, previous_answers=history)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    for t in topics:
        db.add(DiagnosticResult(session_id=session.id, topic=t["topic"],
                                 ability_score=t["ability_score"], weak=t["weak"]))
    session.status = "completed"
    await db.commit()

    return await _load_result(db, session)


@router.get("/{session_id}/result", response_model=DiagnosticResultOut)
async def get_diagnostic_result(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(DiagnosticSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
    return await _load_result(db, session)


async def _get_answers(db: AsyncSession, session_id: uuid.UUID) -> list[dict]:
    rows = (await db.scalars(select(DiagnosticAnswer).where(DiagnosticAnswer.session_id == session_id))).all()
    return [{"item_id": r.item_id, "answer": r.answer} for r in rows]


async def _load_result(db: AsyncSession, session: DiagnosticSession) -> DiagnosticResultOut:
    rows = (await db.scalars(select(DiagnosticResult).where(DiagnosticResult.session_id == session.id))).all()
    return DiagnosticResultOut(
        status=session.status,
        topics=[TopicResult(topic=r.topic, ability_score=r.ability_score, weak=r.weak) for r in rows],
    )
