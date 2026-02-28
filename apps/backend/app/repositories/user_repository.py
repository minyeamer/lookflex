"""User / Group / RegisterRequest DB 레포지토리"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import Group, RegisterRequest, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.groups))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email).options(selectinload(User.groups))
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user, ["groups"])
        return user

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user


class RegisterRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email_pending(self, email: str) -> Optional[RegisterRequest]:
        from app.db.models.enums import ApprovalStatus
        result = await self.db.execute(
            select(RegisterRequest).where(
                RegisterRequest.email == email,
                RegisterRequest.status == ApprovalStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, request_id: uuid.UUID) -> Optional[RegisterRequest]:
        result = await self.db.execute(
            select(RegisterRequest).where(RegisterRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> RegisterRequest:
        req = RegisterRequest(**kwargs)
        self.db.add(req)
        await self.db.flush()
        return req

    async def list_by_status(
        self,
        status,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[RegisterRequest], int]:
        from sqlalchemy import func

        q = select(RegisterRequest).where(RegisterRequest.status == status)
        total_result = await self.db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        items_result = await self.db.execute(
            q.order_by(RegisterRequest.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return items_result.scalars().all(), total

    async def save(self, req: RegisterRequest) -> RegisterRequest:
        self.db.add(req)
        await self.db.flush()
        return req
