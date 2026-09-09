"""
ИИ-ассистент — чат с RAG-системой (п. 4.4 ТЗ). Тот же паттерн, что и
диагностика: backend хранит сессии и историю сообщений, генерацию ответа
делегирует ИИ-сервису Валентины (docs/ai-service-contract.md, раздел 1).
Работает в mock-режиме (AI_SERVICE_MOCK=true), пока её сервис не задеплоен.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.ai_client import AIServiceError, get_chat_answer
from app.db.session import get_db
from app.models.assistant import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.assistant import ChatMessageOut, ChatRequest, ChatResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.session_id:
        session = await db.get(ChatSession, payload.session_id)
        if not session or session.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
    else:
        if not payload.subject:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Для новой сессии укажите subject",
            )
        session = ChatSession(user_id=user.id, subject=payload.subject)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    history_rows = (
        await db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at)
        )
    ).all()
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    await db.commit()

    try:
        result = await get_chat_answer(str(user.id), session.subject, payload.message, history)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=result["answer"])
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=session.id,
        answer=result["answer"],
        sources=result.get("sources", []),
    )


@router.get("/sessions/{session_id}/history", response_model=list[ChatMessageOut])
async def get_history(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")

    rows = (
        await db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        )
    ).all()
    return rows
