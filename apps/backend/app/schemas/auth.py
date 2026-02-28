"""Auth 도메인 Pydantic 스키마"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.models.enums import ApprovalStatus, Role


# ── 이메일 인증 (회원가입 이전 단계) ─────────────────────────────────────────

class SendVerificationRequest(BaseModel):
    email: EmailStr


# ── 회원가입 ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    requested_role: Role = Role.VIEWER

    @field_validator("requested_role")
    @classmethod
    def role_must_be_non_admin(cls, v: Role) -> Role:
        if v not in (Role.EDITOR, Role.VIEWER):
            raise ValueError("EDITOR 또는 VIEWER만 선택 가능합니다.")
        return v


class RegisterResponse(BaseModel):
    message: str
    email: str


# ── 이메일 인증 ───────────────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResendCodeRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


# ── 로그인 ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


# ── 회원가입 요청 관리 (ADMIN) ────────────────────────────────────────────────

class RegisterRequestItem(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    requested_role: Role
    status: ApprovalStatus
    email_verified_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessRegisterRequest(BaseModel):
    status: ApprovalStatus
    assigned_role: Optional[Role] = None
    reject_reason: Optional[str] = None

    @field_validator("assigned_role")
    @classmethod
    def check_assigned_role(cls, v: Optional[Role], info) -> Optional[Role]:
        # 승인 시 assigned_role 필수, EDITOR | VIEWER만 가능
        status = info.data.get("status")
        if status == ApprovalStatus.APPROVED:
            if v is None:
                raise ValueError("승인 시 assignedRole이 필요합니다.")
            if v not in (Role.EDITOR, Role.VIEWER):
                raise ValueError("EDITOR 또는 VIEWER만 부여 가능합니다.")
        return v


class ProcessRegisterResponse(BaseModel):
    user_id: Optional[uuid.UUID] = None
    status: ApprovalStatus


# ── 비밀번호 재설정 ───────────────────────────────────────────────────────────

class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetBody(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=100)
