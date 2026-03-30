"""User 도메인 비즈니스 로직"""
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models.enums import Role
from app.db.models.user import User
from app.repositories.user_repository import GroupRepository, UserRepository
from app.schemas.user import (
    PasswordChangeRequest,
    ProfileUpdateRequest,
    UserProfileUpdate,
    UserRoleUpdate,
)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.group_repo = GroupRepository(db)

    async def update_profile(
        self,
        user: User,
        data: ProfileUpdateRequest,
    ) -> User:
        """내 프로필 수정"""
        if data.name is not None:
            user.name = data.name
        if data.profile_image_url is not None:
            user.profile_image_url = data.profile_image_url

        await self.user_repo.save(user)
        await self.db.commit()
        await self.db.refresh(user, ["groups"])
        return user

    async def change_password(
        self,
        user: User,
        data: PasswordChangeRequest,
    ) -> None:
        """내 비밀번호 변경"""
        # 현재 비밀번호 확인
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_PASSWORD",
                        "message": "현재 비밀번호가 일치하지 않습니다.",
                    },
                },
            )

        # 새 비밀번호 설정
        user.hashed_password = hash_password(data.new_password)
        await self.user_repo.save(user)
        await self.db.commit()

    async def list_users(
        self,
        search: Optional[str] = None,
        role: Optional[Role] = None,
        group_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """사용자 목록 조회 (ADMIN 전용)"""
        users, total = await self.user_repo.list_users(
            search=search,
            role=role,
            group_id=group_id,
            page=page,
            limit=limit,
        )
        return users, total

    async def get_user(self, user_id: uuid.UUID) -> User:
        """사용자 단건 조회 (ADMIN 전용)"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "사용자를 찾을 수 없습니다.",
                    },
                },
            )
        return user

    async def update_user_roles(
        self,
        current_user: User,
        updates: list[UserRoleUpdate],
    ) -> dict:
        """다중 사용자 역할 수정 (ADMIN 전용)"""
        user_ids = [upd.user_id for upd in updates]
        users = await self.user_repo.get_multiple_by_ids(user_ids)
        user_dict = {u.id: u for u in users}

        success_count = 0
        failed = []

        for upd in updates:
            user = user_dict.get(upd.user_id)
            if not user:
                failed.append({"user_id": str(upd.user_id), "reason": "사용자를 찾을 수 없습니다."})
                continue

            # OWNER 역할은 변경 불가
            if user.role == Role.OWNER:
                failed.append({"user_id": str(upd.user_id), "reason": "OWNER 역할은 변경할 수 없습니다."})
                continue

            # 본인 역할은 변경 불가
            if user.id == current_user.id:
                failed.append({"user_id": str(upd.user_id), "reason": "본인의 역할은 변경할 수 없습니다."})
                continue

            user.role = upd.role
            await self.user_repo.save(user)
            success_count += 1

        await self.db.commit()
        return {"success_count": success_count, "failed": failed if failed else None}

    async def update_user_profiles(
        self,
        updates: list[UserProfileUpdate],
    ) -> dict:
        """다중 사용자 그룹/프로필 수정 (ADMIN 전용)"""
        user_ids = [upd.user_id for upd in updates]
        users = await self.user_repo.get_multiple_by_ids(user_ids)
        user_dict = {u.id: u for u in users}

        # 모든 그룹 ID 수집 및 조회
        all_group_ids = []
        for upd in updates:
            if upd.groups:
                all_group_ids.extend(upd.groups)
        all_group_ids = list(set(all_group_ids))  # 중복 제거

        groups = []
        if all_group_ids:
            groups = await self.group_repo.get_multiple_by_ids(all_group_ids)
        group_dict = {g.id: g for g in groups}

        success_count = 0
        failed = []

        for upd in updates:
            user = user_dict.get(upd.user_id)
            if not user:
                failed.append({"user_id": str(upd.user_id), "reason": "사용자를 찾을 수 없습니다."})
                continue

            # 이름 변경
            if upd.name is not None:
                user.name = upd.name

            # 프로필 이미지 변경
            if upd.profile_image_url is not None:
                user.profile_image_url = upd.profile_image_url

            # 그룹 변경
            if upd.groups is not None:
                new_groups = [group_dict[gid] for gid in upd.groups if gid in group_dict]
                user.groups = new_groups

            await self.user_repo.save(user)
            success_count += 1

        await self.db.commit()
        return {"success_count": success_count, "failed": failed if failed else None}

    async def deactivate_user(
        self,
        current_user: User,
        user_id: uuid.UUID,
    ) -> None:
        """사용자 비활성화 (ADMIN 전용)"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "사용자를 찾을 수 없습니다.",
                    },
                },
            )

        # OWNER는 비활성화 불가
        if user.role == Role.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "CANNOT_DEACTIVATE_OWNER",
                        "message": "OWNER 계정은 비활성화할 수 없습니다.",
                    },
                },
            )

        # 본인은 비활성화 불가
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "CANNOT_DEACTIVATE_SELF",
                        "message": "본인 계정은 비활성화할 수 없습니다.",
                    },
                },
            )

        user.is_active = False
        await self.user_repo.save(user)
        await self.db.commit()
