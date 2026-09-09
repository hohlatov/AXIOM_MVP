import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_password_reset_email
from app.core.rate_limit import rate_limit_by_ip, rate_limit_by_key
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.vk_oauth import build_authorize_url, exchange_code
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenPair,
    UserLogin,
    UserOut,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

PASSWORD_RESET_TTL_SECONDS = 30 * 60
PASSWORD_RESET_KEY_PREFIX = "pwdreset:"


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_by_ip("register", max_requests=5, window_seconds=3600))],
)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        grade=payload.grade,
        parental_consent_given=True,
        parental_consent_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit_by_ip("login", max_requests=8, window_seconds=900))],
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    # Отдельный лимит по email — защищает конкретный аккаунт от перебора,
    # даже если атакующий распределяет попытки по разным IP.
    await rate_limit_by_key("login-email", payload.email, max_requests=5, window_seconds=900)

    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user


@router.get("/me", response_model=UserOut)
async def read_current_user(user: User = Depends(get_current_user)):
    return user


# ---------- VK ID ----------

@router.get("/vk/login")
async def vk_login():
    """Отдаёт фронтенду URL для редиректа на VK OAuth."""
    state = secrets.token_urlsafe(16)
    return {"authorize_url": build_authorize_url(state), "state": state}


@router.get(
    "/vk/callback",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit_by_ip("vk-callback", max_requests=20, window_seconds=3600))],
)
async def vk_callback(code: str, parental_consent: bool, db: AsyncSession = Depends(get_db)):
    try:
        vk_data = await exchange_code(code)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось авторизоваться через VK")

    vk_id = str(vk_data["user_id"])
    email = vk_data.get("email")

    user = await db.scalar(select(User).where(User.vk_id == vk_id))
    if not user:
        # Если VK отдал email и он уже занят обычной регистрацией — привязываем VK к тому же аккаунту
        if email:
            user = await db.scalar(select(User).where(User.email == email))
        is_new_account = user is None
        if is_new_account:
            if not parental_consent:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Для регистрации требуется согласие родителя/законного представителя "
                           "на обработку персональных данных",
                )
            user = User(
                vk_id=vk_id, email=email,
                parental_consent_given=True, parental_consent_at=datetime.now(timezone.utc),
            )
            db.add(user)
        else:
            user.vk_id = vk_id
        await db.commit()
        await db.refresh(user)

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ---------- Восстановление пароля ----------

@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_by_ip("pwreset-request", max_requests=5, window_seconds=3600))],
)
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    await rate_limit_by_key("pwreset-request-email", payload.email, max_requests=3, window_seconds=3600)

    user = await db.scalar(select(User).where(User.email == payload.email))
    # Намеренно не сообщаем, найден email или нет — иначе можно перебором узнать,
    # кто зарегистрирован. Ответ 202 одинаковый в обоих случаях.
    if user:
        token = secrets.token_urlsafe(32)
        redis = get_redis()
        await redis.setex(f"{PASSWORD_RESET_KEY_PREFIX}{token}", PASSWORD_RESET_TTL_SECONDS, str(user.id))
        reset_link = f"{settings.frontend_url}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_link)
    return {"detail": "Если email зарегистрирован, письмо с инструкцией отправлено"}


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit_by_ip("pwreset-confirm", max_requests=15, window_seconds=3600))],
)
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    redis = get_redis()
    key = f"{PASSWORD_RESET_KEY_PREFIX}{payload.token}"
    user_id = await redis.get(key)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ссылка недействительна или истекла")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь не найден")

    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    await redis.delete(key)  # токен одноразовый
    return {"detail": "Пароль обновлён"}
