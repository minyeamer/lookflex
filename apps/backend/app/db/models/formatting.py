import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.enums import CondFormatApplyTo, FilterOp

if TYPE_CHECKING:
    from app.db.models.chart import Chart


class ConditionalFormat(Base):
    """차트에 적용된 조건부 서식 묶음"""

    __tablename__ = "conditional_formats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # 서식 평가 순서 (낮을수록 먼저 적용)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    apply_to: Mapped[CondFormatApplyTo] = mapped_column(
        Enum(CondFormatApplyTo), nullable=False, default=CondFormatApplyTo.CELL
    )
    # 조건 판단 대상 필드 ID 목록
    target_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    chart: Mapped["Chart"] = relationship("Chart", back_populates="conditional_formats")
    rules: Mapped[List["ConditionalFormatRule"]] = relationship(
        "ConditionalFormatRule",
        back_populates="format",
        cascade="all, delete-orphan",
        order_by="ConditionalFormatRule.order",
    )


class ConditionalFormatRule(Base):
    """조건부 서식 내 단일 규칙 (operator + value + style)"""

    __tablename__ = "conditional_format_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conditional_formats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    operator: Mapped[FilterOp] = mapped_column(Enum(FilterOp), nullable=False)
    # 비교 값 (숫자, 문자열, null 모두 지원)
    value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # BETWEEN 연산자 사용 시 상한값
    second_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # {backgroundColor, color, fontWeight, fontStyle, textDecoration}
    style: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # relationships
    format: Mapped["ConditionalFormat"] = relationship("ConditionalFormat", back_populates="rules")
