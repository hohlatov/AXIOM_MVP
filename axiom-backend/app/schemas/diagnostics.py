import uuid

from pydantic import BaseModel


class DiagnosticItem(BaseModel):
    item_id: str | None
    question: str | None
    options: list[str] | None
    is_final: bool


class StartDiagnosticOut(BaseModel):
    session_id: uuid.UUID
    item: DiagnosticItem


class AnswerIn(BaseModel):
    session_id: uuid.UUID
    item_id: str
    answer: str


class TopicResult(BaseModel):
    topic: str
    ability_score: float
    weak: bool


class DiagnosticResultOut(BaseModel):
    status: str
    topics: list[TopicResult]
