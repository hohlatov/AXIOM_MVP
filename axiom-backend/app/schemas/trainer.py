import uuid

from pydantic import BaseModel, Field


class TrainerTaskOut(BaseModel):
    """Без correct_answer и explanation — их отдаём только после ответа."""
    id: uuid.UUID
    subject: str
    topic: str
    difficulty: int
    question: str
    options: list[str] | None

    class Config:
        from_attributes = True


class SubmitAnswer(BaseModel):
    task_id: uuid.UUID
    answer: str = Field(min_length=1, max_length=255)


class SubmitResult(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
