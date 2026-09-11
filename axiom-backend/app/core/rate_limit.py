"""
Rate limiting на основе Redis (fixed window). Ничего нового не добавляем в
зависимости — используем тот же Redis, что и для одноразовых токенов сброса
пароля.

Два способа применения:
  - rate_limit_by_ip(...) — FastAPI-зависимость, ограничивает по IP клиента.
    Подключается через dependencies=[Depends(...)] в декораторе роута.
  - rate_limit_by_key(...) — прямой вызов внутри тела эндпоинта, для
    ограничения по идентификатору, который известен только после парсинга
    запроса (например, email из payload). Защищает конкретный аккаунт от
    перебора, даже если атакующий распределяет запросы по многим IP.

За обратным прокси (на проде — RelaxDev) request.client.host будет адресом
прокси, а не реального клиента — поэтому берём IP из X-Forwarded-For, если
заголовок присутствует (см. _get_client_ip). Это защищает только от
поведения "все пользователи делят один и тот же лимит", но не является
надёжной защитой от подделки самого заголовка — она верна ровно настолько,
насколько прокси перед приложением гарантированно перезаписывает (а не
добавляет к) X-Forwarded-For, пришедший от клиента. Это не проверялось
динамически против прод-инфраструктуры (см. docs/security/security-audit.md,
находка 3) — при наличии доступа к конфигурации RelaxDev стоит подтвердить
это поведение отдельно.
"""
from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Конвенция: прокси добавляет IP клиента в конец существующего списка,
        # поэтому самый левый адрес — тот, что был в запросе до первого хопа.
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check(redis_key: str, max_requests: int, window_seconds: int) -> None:
    redis = get_redis()
    count = await redis.incr(redis_key)
    if count == 1:
        await redis.expire(redis_key, window_seconds)
    if count > max_requests:
        ttl = await redis.ttl(redis_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Попробуйте позже.",
            headers={"Retry-After": str(max(ttl, 1))},
        )


def rate_limit_by_ip(key: str, max_requests: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        client_ip = _get_client_ip(request)
        await _check(f"ratelimit:{key}:ip:{client_ip}", max_requests, window_seconds)

    return dependency


async def rate_limit_by_key(key: str, identifier: str, max_requests: int, window_seconds: int) -> None:
    await _check(f"ratelimit:{key}:{identifier.lower()}", max_requests, window_seconds)
