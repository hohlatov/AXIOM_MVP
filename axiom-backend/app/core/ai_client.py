"""
Клиент к ИИ-сервису Валентины (docs/ai-service-contract.md).

AI_SERVICE_MOCK=true (по умолчанию в dev) — не ходит по сети, возвращает
детерминированные тестовые данные, чтобы диагностику можно было гонять
end-to-end уже сейчас, до того как её сервис задеплоен. В проде выставить
AI_SERVICE_MOCK=false — тогда все вызовы идут по HTTP на AI_SERVICE_URL.
"""
import httpx

from app.core.config import settings


class AIServiceError(Exception):
    pass


# Небольшой фиксированный банк вопросов для mock-режима — только для локальной
# разработки/тестов, не настоящая CAT/IRT-логика (та будет на стороне Валентины).
_MOCK_ITEMS = {
    "math": [
        {"item_id": "mock-1", "question": "2 + 2 * 2 = ?", "options": ["6", "8"]},
        {"item_id": "mock-2", "question": "Корень из 16?", "options": ["4", "8"]},
        {"item_id": "mock-3", "question": "10% от 50?", "options": ["5", "10"]},
    ],
}


async def get_next_item(session_id: str, subject: str, previous_answers: list[dict]) -> dict:
    """previous_answers: [{"item_id": "...", "answer": "..."}] — сырые ответы,
    без признака корректности (см. ai-service-contract.md, раздел 2)."""
    if settings.ai_service_mock:
        items = _MOCK_ITEMS.get(subject, _MOCK_ITEMS["math"])
        idx = len(previous_answers)
        if idx >= len(items):
            return {"item_id": None, "question": None, "options": None, "is_final": True}
        item = items[idx]
        return {**item, "is_final": False}

    payload = {"session_id": session_id, "subject": subject, "previous_answers": previous_answers}
    async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
        try:
            resp = await client.post(f"{settings.ai_service_url}/v1/diagnostics/next-item", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise AIServiceError(f"AI-сервис недоступен: {e}") from e
    return resp.json()


async def finalize_session(session_id: str, subject: str, previous_answers: list[dict]) -> list[dict]:
    if settings.ai_service_mock:
        # фиктивная карта пробелов — только для локальной разработки
        return [
            {"topic": "Уравнения", "ability_score": 0.72, "weak": False},
            {"topic": "Проценты", "ability_score": 0.35, "weak": True},
        ]

    payload = {"session_id": session_id, "subject": subject, "previous_answers": previous_answers}
    async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
        try:
            resp = await client.post(f"{settings.ai_service_url}/v1/diagnostics/finalize", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise AIServiceError(f"AI-сервис недоступен: {e}") from e
    return resp.json()["topics"]


async def get_chat_answer(user_id: str, subject: str, message: str, history: list[dict]) -> dict:
    """history: [{"role": "user"|"assistant", "content": "..."}] — контракт п.1 ai-service-contract.md."""
    if settings.ai_service_mock:
        # заглушка для локальной разработки/тестов — не настоящий RAG
        return {
            "answer": f"(mock) По теме «{subject}» на вопрос «{message[:60]}» полноценный ответ "
                       f"даст сервис AI. Это тестовая заглушка для проверки интеграции.",
            "sources": [],
            "latency_ms": 5,
        }

    payload = {"user_id": user_id, "subject": subject, "message": message, "history": history}
    async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
        try:
            resp = await client.post(f"{settings.ai_service_url}/v1/assistant/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise AIServiceError(f"AI-сервис недоступен: {e}") from e
    return resp.json()
