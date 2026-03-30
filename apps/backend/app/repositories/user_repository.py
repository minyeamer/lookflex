"""User / Group / RegisterRequest DB 레포지토리"""
import uuid
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import Group, RegisterRequest, User
from app.db.models.enums import Role, GroupType


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

    async def list_users(
        self,
        search: Optional[str] = None,
        role: Optional[Role] = None,
        group_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """사용자 목록 조회 (검색, 필터, 페이지네이션)"""
        q = select(User).options(selectinload(User.groups))

        # 검색 (이름 또는 이메일)
        if search:
            q = q.where(
                or_(
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                )
            )

        # 역할 필터
        if role:
            q = q.where(User.role == role)

        # 그룹 필터
        if group_id:
            q = q.join(User.groups).where(Group.id == group_id)

        # 총 개수
        total_result = await self.db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        # 페이지네이션
        items_result = await self.db.execute(
            q.order_by(User.joined_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return items_result.scalars().all(), total

    async def get_multiple_by_ids(self, user_ids: list[uuid.UUID]) -> list[User]:
        """여러 사용자 ID로 조회"""
        result = await self.db.execute(
            select(User).where(User.id.in_(user_ids)).options(selectinload(User.groups))
        )
        return result.scalars().all()


class GroupRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, group_id: uuid.UUID) -> Optional[Group]:
        result = await self.db.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()

    async def get_multiple_by_ids(self, group_ids: list[uuid.UUID]) -> list[Group]:
        """여러 그룹 ID로 조회"""
        result = await self.db.execute(select(Group).where(Group.id.in_(group_ids)))
        return result.scalars().all()


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
