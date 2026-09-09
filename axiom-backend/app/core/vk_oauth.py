import httpx

from app.core.config import settings

VK_API_VERSION = "5.131"
VK_AUTHORIZE_URL = "https://oauth.vk.com/authorize"
VK_TOKEN_URL = "https://oauth.vk.com/access_token"


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.vk_client_id,
        "redirect_uri": settings.vk_redirect_uri,
        "display": "page",
        "scope": "email",
        "response_type": "code",
        "v": VK_API_VERSION,
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{VK_AUTHORIZE_URL}?{query}"


async def exchange_code(code: str) -> dict:
    """Возвращает {'access_token', 'user_id', 'email' (может отсутствовать)}."""
    params = {
        "client_id": settings.vk_client_id,
        "client_secret": settings.vk_client_secret,
        "redirect_uri": settings.vk_redirect_uri,
        "code": code,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(VK_TOKEN_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(data.get("error_description", "VK OAuth error"))
    return data
