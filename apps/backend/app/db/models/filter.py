import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.enums import FilterOp, FilterType

if TYPE_CHECKING:
    from app.db.models.dashboard import Page
    from app.db.models.datasource import DataSource


class Filter(Base):
    """페이지 내 배치되는 인터랙티브 필터 UI 요소"""

    __tablename__ = "filters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    datasource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True
    )
    # 데이터소스 내 필드 식별자 (fieldId)
    field_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    type: Mapped[FilterType] = mapped_column(Enum(FilterType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 배치 좌표 및 크기 (px)
    x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    # 타입별 설정 (defaultValue, applyTo, operator 등)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    page: Mapped["Page"] = relationship("Page", back_populates="filters")
    datasource: Mapped[Optional["DataSource"]] = relationship("DataSource")


class DefaultFilterRule(Base):
    """페이지 또는 특정 차트에 항상 적용되는 고정 필터 규칙"""

    __tablename__ = "default_filter_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "PAGE" 또는 chart_id (UUID 문자열)
    apply_to: Mapped[str] = mapped_column(String(200), nullable=False)
    datasource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[FilterOp] = mapped_column(Enum(FilterOp), nullable=False)
    # 단일 값, 배열, 숫자 모두 수용하기 위해 JSONB 사용
    value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # relationships
    page: Mapped["Page"] = relationship("Page")
    datasource: Mapped["DataSource"] = relationship("DataSource")
