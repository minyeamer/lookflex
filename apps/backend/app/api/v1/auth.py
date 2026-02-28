"""Auth API 라우터 — /api/v1/auth/*"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentUser, require_role
from app.db.models.enums import ApprovalStatus, Role
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetBody,
    PasswordResetRequestBody,
    ProcessRegisterRequest,
    ProcessRegisterResponse,
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    SendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
    RegisterRequestItem,
)
from app.schemas.common import ApiResponse, PaginatedData
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)


# ── 회원가입 ──────────────────────────────────────────────────────────────────
@router.post("/send-verification", response_model=ApiResponse[MessageResponse])
async def send_verification(
    body: SendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """1단계: 이메일만 입력해 OTP 요청. DB 기록 없음."""
    data = await AuthService(db).send_verification(body.email)
    return ApiResponse.ok(data)

@router.post("/register", response_model=ApiResponse[RegisterResponse], status_code=201)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).register(body)
    return ApiResponse.ok(data)


@router.post("/verify-email", response_model=ApiResponse[MessageResponse])
async def verify_email(
    body: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).verify_email(body)
    return ApiResponse.ok(data)


@router.post("/resend-code", response_model=ApiResponse[MessageResponse])
async def resend_code(
    body: ResendCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).resend_code(body.email)
    return ApiResponse.ok(data)


# ── 로그인 / 토큰 ─────────────────────────────────────────────────────────────

@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token_data, refresh_token = await AuthService(db).login(body)
    _set_refresh_cookie(response, refresh_token)
    return ApiResponse.ok(token_data)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail={"code": "NO_REFRESH_TOKEN", "message": "Refresh Token이 없습니다."})
    data = await AuthService(db).refresh(refresh_token)
    return ApiResponse.ok(data)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    _clear_refresh_cookie(response)


# ── 회원가입 요청 관리 (ADMIN) ─────────────────────────────────────────────────

@router.get(
    "/register-requests",
    response_model=ApiResponse[PaginatedData[RegisterRequestItem]],
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
async def list_register_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    req_status: ApprovalStatus = Query(default=ApprovalStatus.PENDING, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    data = await AuthService(db).list_register_requests(req_status, page, limit)
    return ApiResponse.ok(data)


@router.patch(
    "/register-requests/{request_id}",
    response_model=ApiResponse[ProcessRegisterResponse],
    dependencies=[Depends(require_role(Role.ADMIN, Role.OWNER))],
)
async def process_register_request(
    request_id: uuid.UUID,
    body: ProcessRegisterRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).process_register_request(request_id, body, current_user)
    return ApiResponse.ok(data)


# ── 비밀번호 재설정 ───────────────────────────────────────────────────────────

@router.post("/password-reset-request", response_model=ApiResponse[MessageResponse])
async def password_reset_request(
    body: PasswordResetRequestBody,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).password_reset_request(body)
    return ApiResponse.ok(data)


@router.post("/password-reset", response_model=ApiResponse[MessageResponse])
async def password_reset(
    body: PasswordResetBody,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await AuthService(db).password_reset(body)
    return ApiResponse.ok(data)
