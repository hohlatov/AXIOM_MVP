from pydantic import BaseModel


class SubjectProgress(BaseModel):
    subject: str          # "math" | "russian"
    subject_label: str    # "Математика" | "Русский язык"
    percent: int           # 0-100, из результатов диагностики (пока — заглушка)


class Recommendation(BaseModel):
    topic: str
    reason: str


class DashboardSummary(BaseModel):
    grade: int | None
    progress: list[SubjectProgress]
    recommendations: list[Recommendation]
    quick_actions: list[str]  # какие разделы доступны прямо сейчас
    has_diagnostic_result: bool
