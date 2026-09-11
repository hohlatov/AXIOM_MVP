"""
Адаптивный тренажёр с разбором ошибок — базовая версия (п. 4.3 ТЗ).

Подбор задания пока НЕ использует результаты диагностики (модуль диагностики
ещё не реализован): вместо этого next-task ориентируется на историю ответов
самого тренажёра — темы, где ученик чаще ошибался или ещё не пробовал,
получают приоритет. Когда появится DiagnosticResult, здесь нужно подмешать
её в выбор темы (см. TODO ниже) — контракт эндпоинтов менять не придётся.
"""
import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.answer_check import answers_match
from app.db.session import get_db
from app.models.knowledge import KnowledgeState
from app.models.trainer import TaskAttempt, TrainerTask
from app.models.user import User
from app.schemas.trainer import SkillMapTopic, SubmitAnswer, SubmitResult, TrainerTaskOut

router = APIRouter(prefix="/trainer", tags=["trainer"])

KNOWLEDGE_STATE_DECAY = 0.8  # см. docs/architecture/adaptive-learning-engine.md — EWMA, не ML


async def _update_knowledge_state(db: AsyncSession, user: User, task: TrainerTask, is_correct: bool) -> None:
    """Живая карта навыков (killer feature) — детерминированная EWMA-оценка
    владения темой, обновляемая после каждой попытки. new = old*0.8 + result*0.2;
    на первой попытке по теме — просто сам результат, без фиктивной базовой линии."""
    result = 1.0 if is_correct else 0.0
    state = await db.scalar(
        select(KnowledgeState).where(
            KnowledgeState.user_id == user.id,
            KnowledgeState.subject == task.subject,
            KnowledgeState.topic == task.topic,
        )
    )
    if state is None:
        db.add(KnowledgeState(
            user_id=user.id, subject=task.subject, topic=task.topic,
            ability_score=result, attempts_count=1,
        ))
    else:
        state.ability_score = state.ability_score * KNOWLEDGE_STATE_DECAY + result * (1 - KNOWLEDGE_STATE_DECAY)
        state.attempts_count += 1


async def _pick_topic(db: AsyncSession, user: User, subject: str) -> str | None:
    all_topics = (
        await db.scalars(select(TrainerTask.topic).where(TrainerTask.subject == subject).distinct())
    ).all()
    if not all_topics:
        return None

    # точность по темам на основе попыток этого пользователя
    rows = (
        await db.execute(
            select(
                TrainerTask.topic,
                func.count(TaskAttempt.id).label("attempts"),
                func.sum(func.cast(TaskAttempt.is_correct, Integer)).label("correct"),
            )
            .join(TaskAttempt, TaskAttempt.task_id == TrainerTask.id)
            .where(TrainerTask.subject == subject, TaskAttempt.user_id == user.id)
            .group_by(TrainerTask.topic)
        )
    ).all()
    stats = {topic: (attempts, correct or 0) for topic, attempts, correct in rows}

    # TODO: когда будет DiagnosticResult — темы, помеченные там как "weak",
    # должны получать приоритет независимо от истории тренажёра.

    unattempted = [t for t in all_topics if t not in stats]
    if unattempted:
        return random.choice(unattempted)

    # тема с наименьшей долей правильных ответов — приоритет
    def accuracy(topic):
        attempts, correct = stats[topic]
        return correct / attempts if attempts else 0

    return min(all_topics, key=accuracy)


@router.get("/next-task", response_model=TrainerTaskOut)
async def next_task(
    subject: str = Query(pattern="^(math|russian)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    topic = await _pick_topic(db, user, subject)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Для этого предмета пока нет заданий")

    # среди задач темы предпочитаем те, что пользователь ещё не решил верно
    solved_ids = (
        await db.scalars(
            select(TaskAttempt.task_id).where(TaskAttempt.user_id == user.id, TaskAttempt.is_correct.is_(True))
        )
    ).all()

    candidates = (
        await db.scalars(select(TrainerTask).where(TrainerTask.subject == subject, TrainerTask.topic == topic))
    ).all()
    unsolved = [t for t in candidates if t.id not in solved_ids]
    task = random.choice(unsolved) if unsolved else random.choice(candidates)
    return task


@router.post("/submit", response_model=SubmitResult)
async def submit_answer(
    payload: SubmitAnswer,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(TrainerTask, payload.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")

    is_correct = answers_match(payload.answer, task.correct_answer)

    attempt = TaskAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        task_id=task.id,
        submitted_answer=payload.answer,
        is_correct=is_correct,
    )
    db.add(attempt)
    await _update_knowledge_state(db, user, task, is_correct)
    await db.commit()

    return SubmitResult(is_correct=is_correct, correct_answer=task.correct_answer, explanation=task.explanation)


@router.get("/skill-map", response_model=list[SkillMapTopic])
async def skill_map(
    subject: str = Query(pattern="^(math|russian)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Живая карта навыков ученика — по каждой теме предмета: уровень владения
    (EWMA по попыткам в тренажёре) и число попыток. Темы, которых ученик ещё
    не касался, тоже возвращаются (ability_score=null, attempts_count=0), чтобы
    UI мог честно показать «не начато», а не молчать о существовании темы."""
    all_topics = (
        await db.scalars(select(TrainerTask.topic).where(TrainerTask.subject == subject).distinct())
    ).all()

    states = (
        await db.scalars(
            select(KnowledgeState).where(KnowledgeState.user_id == user.id, KnowledgeState.subject == subject)
        )
    ).all()
    by_topic = {s.topic: s for s in states}

    return [
        SkillMapTopic(
            topic=topic,
            ability_score=by_topic[topic].ability_score if topic in by_topic else None,
            attempts_count=by_topic[topic].attempts_count if topic in by_topic else 0,
        )
        for topic in sorted(all_topics)
    ]
