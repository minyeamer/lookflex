"""Auth 비즈니스 로직"""
import random
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis, otp_key, pw_reset_key
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.enums import ApprovalStatus, Role
from app.db.models.user import User
from app.repositories.user_repository import RegisterRequestRepository, UserRepository
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetBody,
    PasswordResetRequestBody,
    ProcessRegisterRequest,
    ProcessRegisterResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.email_service import (
    send_approval_result_email,
    send_otp_email,
    send_password_reset_email,
)

OTP_TTL = 10 * 60  # 10분
PW_RESET_TTL = 60 * 60  # 1시간


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.req_repo = RegisterRequestRepository(db)
        self.redis = get_redis()

    # ── 회원가입 ──────────────────────────────────────────────────────────────

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        # 이미 가입된 이메일
        if await self.user_repo.get_by_email(body.email):
            raise HTTPException(status_code=409, detail={"code": "EMAIL_ALREADY_EXISTS", "message": "이미 가입된 이메일입니다."})

        # 이미 대기 중인 요청
        if await self.req_repo.get_by_email_pending(body.email):
            raise HTTPException(status_code=409, detail={"code": "REGISTER_REQUEST_PENDING", "message": "동일 이메일로 대기 중인 요청이 있습니다."})

        hashed = hash_password(body.password)
        await self.req_repo.create(
            email=body.email,
            name=body.name,
            hashed_password=hashed,
            requested_role=body.requested_role,
        )
        await self.db.commit()

        # OTP 생성 및 저장
        otp = _generate_otp()
        await self.redis.setex(otp_key(body.email), OTP_TTL, otp)

        # 이메일 발송 (비동기, 실패해도 rollback 없음)
        import asyncio
        asyncio.create_task(send_otp_email(body.email, body.name, otp))

        return RegisterResponse(message="이메일 인증 코드가 발송되었습니다.", email=body.email)

    # ── 이메일 인증 ───────────────────────────────────────────────────────────

    async def verify_email(self, body: VerifyEmailRequest) -> MessageResponse:
        stored = await self.redis.get(otp_key(body.email))
        if not stored:
            raise HTTPException(status_code=400, detail={"code": "CODE_EXPIRED", "message": "인증 코드가 만료되었습니다."})
        if stored != body.code:
            raise HTTPException(status_code=400, detail={"code": "INVALID_CODE", "message": "인증 코드가 일치하지 않습니다."})

        req = await self.req_repo.get_by_email_pending(body.email)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "REQUEST_NOT_FOUND", "message": "가입 요청을 찾을 수 없습니다."})

        req.email_verified_at = datetime.now(timezone.utc)
        await self.req_repo.save(req)
        await self.db.commit()
        await self.redis.delete(otp_key(body.email))

        return MessageResponse(message="이메일 인증이 완료되었습니다. 관리자 승인을 기다려주세요.")

    # ── OTP 재발송 ────────────────────────────────────────────────────────────

    async def resend_code(self, email: str) -> MessageResponse:
        req = await self.req_repo.get_by_email_pending(email)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "REQUEST_NOT_FOUND", "message": "가입 요청을 찾을 수 없습니다."})

        otp = _generate_otp()
        await self.redis.setex(otp_key(email), OTP_TTL, otp)

        import asyncio
        asyncio.create_task(send_otp_email(email, req.name, otp))

        return MessageResponse(message="인증 코드가 재발송되었습니다.")

    # ── 로그인 ────────────────────────────────────────────────────────────────

    async def login(self, body: LoginRequest) -> tuple[TokenResponse, str]:
        """(TokenResponse, refresh_token) 반환"""
        user = await self.user_repo.get_by_email(body.email)

        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 올바르지 않습니다."})

        if not user.email_verified_at:
            raise HTTPException(status_code=403, detail={"code": "EMAIL_NOT_VERIFIED", "message": "이메일 인증이 필요합니다."})

        if not user.is_active:
            raise HTTPException(status_code=403, detail={"code": "ACCOUNT_DISABLED", "message": "비활성화된 계정입니다."})

        from app.core.config import settings
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return (
            TokenResponse(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            refresh_token,
        )

    # ── 토큰 갱신 ─────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> TokenResponse:
        from app.core.security import decode_token
        from app.core.config import settings

        user_id = decode_token(refresh_token, token_type="refresh")
        if not user_id:
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."})

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다."})

        access_token = create_access_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── 회원가입 요청 목록 (ADMIN) ────────────────────────────────────────────

    async def list_register_requests(
        self,
        status: ApprovalStatus = ApprovalStatus.PENDING,
        page: int = 1,
        limit: int = 20,
    ):
        from app.schemas.common import PaginatedData
        from app.schemas.auth import RegisterRequestItem

        items, total = await self.req_repo.list_by_status(status, page, limit)
        return PaginatedData.build(
            items=[RegisterRequestItem.model_validate(r) for r in items],
            total=total,
            page=page,
            limit=limit,
        )

    # ── 회원가입 요청 처리 (ADMIN) ─────────────────────────────────────────────

    async def process_register_request(
        self,
        request_id: uuid.UUID,
        body: ProcessRegisterRequest,
        processed_by: User,
    ) -> ProcessRegisterResponse:
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "요청을 찾을 수 없습니다."})
        if req.status != ApprovalStatus.PENDING:
            raise HTTPException(status_code=409, detail={"code": "ALREADY_PROCESSED", "message": "이미 처리된 요청입니다."})

        req.status = body.status
        req.processed_by_id = processed_by.id
        req.processed_at = datetime.now(timezone.utc)

        new_user_id: Optional[uuid.UUID] = None

        if body.status == ApprovalStatus.APPROVED:
            req.reject_reason = None
            new_user = await self.user_repo.create(
                email=req.email,
                name=req.name,
                hashed_password=req.hashed_password,
                role=body.assigned_role,
                email_verified_at=req.email_verified_at,
            )
            new_user_id = new_user.id
            import asyncio
            asyncio.create_task(send_approval_result_email(req.email, req.name, True))
        else:
            req.reject_reason = body.reject_reason
            import asyncio
            asyncio.create_task(
                send_approval_result_email(req.email, req.name, False, body.reject_reason or "")
            )

        await self.req_repo.save(req)
        await self.db.commit()

        return ProcessRegisterResponse(user_id=new_user_id, status=body.status)

    # ── 비밀번호 재설정 ───────────────────────────────────────────────────────

    async def password_reset_request(self, body: PasswordResetRequestBody) -> MessageResponse:
        user = await self.user_repo.get_by_email(body.email)
        if user:
            token = secrets.token_urlsafe(32)
            await self.redis.setex(pw_reset_key(token), PW_RESET_TTL, str(user.id))
            reset_url = f"http://localhost:3000/reset-password?token={token}"
            import asyncio
            asyncio.create_task(send_password_reset_email(user.email, user.name, reset_url))

        return MessageResponse(message="등록된 이메일인 경우 재설정 링크가 발송됩니다.")

    async def password_reset(self, body: PasswordResetBody) -> MessageResponse:
        user_id_str = await self.redis.get(pw_reset_key(body.token))
        if not user_id_str:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "유효하지 않거나 만료된 토큰입니다."})

        user = await self.user_repo.get_by_id(uuid.UUID(user_id_str))
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다."})

        user.hashed_password = hash_password(body.new_password)
        await self.user_repo.save(user)
        await self.db.commit()
        await self.redis.delete(pw_reset_key(body.token))

        return MessageResponse(message="비밀번호가 변경되었습니다.")
