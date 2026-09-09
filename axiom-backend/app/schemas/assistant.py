import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: uuid.UUID | None = None  # None = создать новую сессию
    subject: str | None = None  # обязателен, если session_id не передан
    message: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    sources: list[str]


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
