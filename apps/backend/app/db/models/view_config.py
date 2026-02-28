import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.chart import Chart


class UserViewConfig(Base):
    """사용자별 차트 뷰 오버라이드 설정 — 원본 차트 설정에 영향 없음"""

    __tablename__ = "user_view_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # {metrics, sort, columnWidths, frozenColumns, rowsPerPage}
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="view_configs")
    chart: Mapped["Chart"] = relationship("Chart", back_populates="view_configs")

    __table_args__ = (UniqueConstraint("user_id", "chart_id", name="uq_user_chart_view"),)
