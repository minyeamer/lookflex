import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.enums import AggregateType, DSSourceType, FieldType

if TYPE_CHECKING:
    from app.db.models.user import User, Group


class DataSource(Base):
    __tablename__ = "datasources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    # 영문 식별자 (필드 접근 prefix, unique)
    source_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    source_type: Mapped[DSSourceType] = mapped_column(Enum(DSSourceType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 암호화하여 저장 (서비스 레이어에서 처리)
    connection_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # True이면 모든 사용자에게 접근 허용
    allow_all: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    fields: Mapped[List["DataSourceField"]] = relationship(
        "DataSourceField", back_populates="datasource", cascade="all, delete-orphan", order_by="DataSourceField.order"
    )
    permissions: Mapped[List["DataSourcePermission"]] = relationship(
        "DataSourcePermission", back_populates="datasource", cascade="all, delete-orphan"
    )


class DataSourceField(Base):
    __tablename__ = "datasource_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 원본 컬럼명 (쿼리 시 사용)
    field_id: Mapped[str] = mapped_column(String(200), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[FieldType] = mapped_column(Enum(FieldType), nullable=False, default=FieldType.TEXT)
    default_aggregate: Mapped[AggregateType] = mapped_column(
        Enum(AggregateType), nullable=False, default=AggregateType.NONE
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    number_format: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # relationships
    datasource: Mapped["DataSource"] = relationship("DataSource", back_populates="fields")

    __table_args__ = (UniqueConstraint("datasource_id", "field_id", name="uq_datasource_field"),)


class DataSourcePermission(Base):
    """데이터 소스 접근 권한 — 그룹 또는 개별 사용자 단위"""

    __tablename__ = "datasource_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "USER" 또는 "GROUP"
    entity_type: Mapped[str] = mapped_column(String(10), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # relationships
    datasource: Mapped["DataSource"] = relationship("DataSource", back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("datasource_id", "entity_type", "entity_id", name="uq_ds_permission"),
    )
