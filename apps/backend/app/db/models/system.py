import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.enums import AuditAction

if TYPE_CHECKING:
    from app.db.models.user import User


class SmtpConfig(Base):
    """SMTP 이메일 서버 설정 — 싱글턴 (항상 id=1 레코드 사용)"""

    __tablename__ = "smtp_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    # 암호화하여 저장
    encrypted_password: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    from_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    from_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AuditLog(Base):
    """사용자 행동 감사 로그"""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    # 액션별 상세 정보 (chartId, datasourceId 등)
    detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # relationships
    user: Mapped[Optional["User"]] = relationship("User")
