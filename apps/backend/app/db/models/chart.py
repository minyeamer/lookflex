import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.enums import ChartType

if TYPE_CHECKING:
    from app.db.models.dashboard import Page
    from app.db.models.datasource import DataSource
    from app.db.models.formatting import ConditionalFormat
    from app.db.models.view_config import UserViewConfig


class Chart(Base):
    __tablename__ = "charts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    datasource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[ChartType] = mapped_column(Enum(ChartType), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    # 배치 좌표 및 크기 (px)
    x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=400)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    # 차트 타입별 설정 (dimensions, metrics, defaultSort 등)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    # 스타일 설정 (header, body, totalsRow, border 등)
    style: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    page: Mapped["Page"] = relationship("Page", back_populates="charts")
    datasource: Mapped[Optional["DataSource"]] = relationship("DataSource")
    conditional_formats: Mapped[List["ConditionalFormat"]] = relationship(
        "ConditionalFormat",
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by="ConditionalFormat.order",
    )
    view_configs: Mapped[List["UserViewConfig"]] = relationship(
        "UserViewConfig", back_populates="chart", cascade="all, delete-orphan"
    )
    chart_group_items: Mapped[List["ChartGroupItem"]] = relationship(
        "ChartGroupItem", back_populates="chart", cascade="all, delete-orphan"
    )


class ChartGroup(Base):
    """여러 차트를 묶어 이동/크기조정 연동"""

    __tablename__ = "chart_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    page: Mapped["Page"] = relationship("Page")
    items: Mapped[List["ChartGroupItem"]] = relationship(
        "ChartGroupItem", back_populates="chart_group", cascade="all, delete-orphan"
    )


class ChartGroupItem(Base):
    __tablename__ = "chart_group_items"

    chart_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chart_groups.id", ondelete="CASCADE"), primary_key=True
    )
    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charts.id", ondelete="CASCADE"), primary_key=True
    )

    # relationships
    chart_group: Mapped["ChartGroup"] = relationship("ChartGroup", back_populates="items")
    chart: Mapped["Chart"] = relationship("Chart", back_populates="chart_group_items")
