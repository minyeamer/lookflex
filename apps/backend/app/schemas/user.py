"""User 도메인 Pydantic 스키마"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.models.enums import GroupType, Role


class GroupSummary(BaseModel):
    id: uuid.UUID
    name: str
    type: GroupType

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    profile_image_url: Optional[str]
    role: Role
    groups: list[GroupSummary] = []
    joined_at: datetime

    model_config = {"from_attributes": True}


# ── 내 프로필 수정 ──
class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_image_url: Optional[str] = Field(None, max_length=500)


# ── 내 비밀번호 변경 ──
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


# ── 사용자 목록 조회 (ADMIN) ──
class UserListItem(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    profile_image_url: Optional[str]
    role: Role
    groups: list[GroupSummary] = []
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


# ── 다중 사용자 역할 수정 (ADMIN) ──
class UserRoleUpdate(BaseModel):
    user_id: uuid.UUID
    role: Role

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Role) -> Role:
        if v == Role.OWNER:
            raise ValueError("OWNER 역할은 시스템에서 관리됩니다.")
        return v


class UserRoleUpdateBulkRequest(BaseModel):
    updates: list[UserRoleUpdate] = Field(..., min_length=1)


# ── 다중 사용자 그룹/프로필 수정 (ADMIN) ──
class UserProfileUpdate(BaseModel):
    user_id: uuid.UUID
    groups: Optional[list[uuid.UUID]] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_image_url: Optional[str] = Field(None, max_length=500)


class UserProfileUpdateBulkRequest(BaseModel):
    updates: list[UserProfileUpdate] = Field(..., min_length=1)
