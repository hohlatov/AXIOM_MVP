from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # VK OAuth
    vk_client_id: str = ""
    vk_client_secret: str = ""
    vk_redirect_uri: str = ""

    # Email (пока консольный backend — см. app/core/email.py)
    mail_from: str = "no-reply@axiom.local"
    frontend_url: str = "http://localhost:3000"

    # SMTP (Yandex Cloud Postbox или любой другой SMTP-провайдер).
    # Если smtp_host пуст — email.py падает обратно на консольный backend,
    # так что для локальной разработки ничего настраивать не нужно.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    # AI service (Valentina)
    ai_service_url: str = "http://localhost:8100"
    ai_service_timeout_seconds: int = 20
    ai_service_mock: bool = True  # true = не ходит по сети, отдаёт тестовые данные (см. app/core/ai_client.py)


settings = Settings()
