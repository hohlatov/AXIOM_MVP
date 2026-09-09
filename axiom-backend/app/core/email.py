"""
Абстракция отправки писем.

Если SMTP_HOST не задан (по умолчанию для локальной разработки) — письма
просто пишутся в лог, поток восстановления пароля остаётся полностью
тестируемым без внешних зависимостей. Если SMTP_HOST задан — письма реально
уходят через SMTP. Готово под Yandex Cloud Postbox "из коробки": у него есть
обычный SMTP-интерфейс, отдельного SDK не нужно.

Настройка на проде (после того как аккаунт Yandex Cloud и Postbox готовы):
  SMTP_HOST=postbox.cloud.yandex.net
  SMTP_PORT=587
  SMTP_USERNAME=<получить в консоли Postbox>
  SMTP_PASSWORD=<получить в консоли Postbox>
  MAIL_FROM=<verified-адрес отправителя в Postbox>
Точный хост/порт свериться в актуальной документации Postbox на момент
подключения — сервис молодой, детали могли поменяться.
"""
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("axiom.email")


def _send_smtp_sync(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Восстановление пароля AXIOM"
    body = (
        f"Вы запросили восстановление пароля.\n\n"
        f"Перейдите по ссылке, чтобы задать новый пароль (действует 30 минут):\n"
        f"{reset_link}\n\n"
        f"Если вы не запрашивали восстановление — просто проигнорируйте это письмо."
    )

    if not settings.smtp_host:
        logger.info("Письмо восстановления пароля для %s: %s", to_email, reset_link)
        return

    try:
        await asyncio.to_thread(_send_smtp_sync, to_email, subject, body)
    except Exception:
        # Не роняем запрос пользователя из-за сбоя почтового провайдера —
        # логируем и продолжаем (эндпоинт всё равно всегда отвечает 202).
        logger.exception("Не удалось отправить письмо восстановления пароля для %s", to_email)
