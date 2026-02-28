"""이메일 발송 서비스 (SMTP 미설정 시 콘솔 출력 fallback)"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body_html: str) -> None:
    """SMTP 설정이 없으면 로그에 출력하고 정상 반환합니다."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning(
            "[EMAIL - SMTP 미설정] to=%s | subject=%s | body=%s",
            to, subject, body_html,
        )
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to, subject, body_html)


def _send_sync(to: str, subject: str, body_html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_PORT == 587:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())


# ── 템플릿 ────────────────────────────────────────────────────────────────────

async def send_otp_email(to: str, code: str, name: str = "사용자") -> None:
    subject = "[LookFlex] 이메일 인증 코드"
    body = f"""
    <p>안녕하세요, {name}님.</p>
    <p>아래 인증 코드를 입력해주세요.</p>
    <h2 style="letter-spacing:6px">{code}</h2>
    <p>코드는 10분간 유효합니다.</p>
    """
    await send_email(to, subject, body)


async def send_password_reset_email(to: str, name: str, reset_url: str) -> None:
    subject = "[LookFlex] 비밀번호 재설정"
    body = f"""
    <p>안녕하세요, {name}님.</p>
    <p>아래 링크를 클릭하여 비밀번호를 재설정하세요.</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>링크는 1시간 동안 유효합니다.</p>
    """
    await send_email(to, subject, body)


async def send_approval_result_email(to: str, name: str, approved: bool, reason: str = "") -> None:
    if approved:
        subject = "[LookFlex] 가입 승인 완료"
        body = f"<p>{name}님의 가입 요청이 승인되었습니다. 로그인하여 서비스를 이용하세요.</p>"
    else:
        subject = "[LookFlex] 가입 요청 거절"
        body = f"<p>{name}님의 가입 요청이 거절되었습니다.</p>"
        if reason:
            body += f"<p>사유: {reason}</p>"
    await send_email(to, subject, body)
