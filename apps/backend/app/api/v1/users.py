"""Users API 엔드포인트"""
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_role
from app.db.models.enums import Role
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.user import (
    PasswordChangeRequest,
    ProfileUpdateRequest,
    UserListItem,
    UserProfile,
    UserProfileUpdateBulkRequest,
    UserRoleUpdateBulkRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ── 2.1. 내 프로필 조회 ──
@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_my_profile(current_user: CurrentUser):
    """내 프로필 조회"""
    return ApiResponse.ok(UserProfile.model_validate(current_user))


# ── 2.2. 내 프로필 수정 ──
@router.patch("/me", response_model=ApiResponse[UserProfile])
async def update_my_profile(
    data: ProfileUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """내 프로필 수정"""
    service = UserService(db)
    updated_user = await service.update_profile(current_user, data)
    return ApiResponse.ok(UserProfile.model_validate(updated_user))


# ── 2.3. 프로필 이미지 업로드 ──
@router.post("/me/profile-image", response_model=ApiResponse[dict])
async def upload_profile_image(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """프로필 이미지 업로드 (구현 예시: 파일 저장 생략)"""
    # TODO: 실제 파일 저장 로직 구현 (S3, 로컬 스토리지 등)
    # 현재는 임시 URL 반환
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "지원하지 않는 파일 형식입니다. (jpg/png/webp만 가능)",
                },
            },
        )

    # 임시 URL (실제로는 파일 저장 후 URL 생성)
    temp_url = f"https://storage.example.com/profiles/{current_user.id}/{file.filename}"

    # 사용자 프로필 업데이트
    current_user.profile_image_url = temp_url
    service = UserService(db)
    await service.user_repo.save(current_user)
    await db.commit()

    return ApiResponse.ok({"url": temp_url})


# ── 2.4. 내 비밀번호 변경 ──
@router.patch("/me/password", response_model=ApiResponse[dict])
async def change_my_password(
    data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """내 비밀번호 변경"""
    service = UserService(db)
    await service.change_password(current_user, data)
    return ApiResponse.ok({"message": "비밀번호가 변경되었습니다."})


# ── 2.5. 사용자 목록 조회 (ADMIN 전용) ──
@router.get("", response_model=ApiResponse[PaginatedData[UserListItem]])
async def list_users(
    search: Optional[str] = Query(None, description="이름 또는 이메일 검색"),
    role: Optional[Role] = Query(None, description="역할 필터"),
    group_id: Optional[uuid.UUID] = Query(None, description="그룹 필터"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(Role.ADMIN, Role.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """사용자 목록 조회 (ADMIN 전용)"""
    service = UserService(db)
    users, total = await service.list_users(
        search=search,
        role=role,
        group_id=group_id,
        page=page,
        limit=limit,
    )

    items = [UserListItem.model_validate(u) for u in users]
    return ApiResponse.ok(
        PaginatedData(
            items=items,
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit,
        )
    )


# ── 2.6. 사용자 단건 조회 (ADMIN 전용) ──
@router.get("/{user_id}", response_model=ApiResponse[UserProfile])
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role(Role.ADMIN, Role.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """사용자 단건 조회 (ADMIN 전용)"""
    service = UserService(db)
    user = await service.get_user(user_id)
    return ApiResponse.ok(UserProfile.model_validate(user))


# ── 2.7. 다중 사용자 역할 수정 (ADMIN 전용) ──
@router.patch("/roles", response_model=ApiResponse[dict])
async def update_user_roles(
    data: UserRoleUpdateBulkRequest,
    current_user: User = Depends(require_role(Role.ADMIN, Role.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """다중 사용자 역할 수정 (ADMIN 전용)"""
    service = UserService(db)
    result = await service.update_user_roles(current_user, data.updates)
    return ApiResponse.ok(result)


# ── 2.8. 다중 사용자 그룹/프로필 수정 (ADMIN 전용) ──
@router.patch("/profiles", response_model=ApiResponse[dict])
async def update_user_profiles(
    data: UserProfileUpdateBulkRequest,
    current_user: User = Depends(require_role(Role.ADMIN, Role.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """다중 사용자 그룹/프로필 수정 (ADMIN 전용)"""
    service = UserService(db)
    result = await service.update_user_profiles(data.updates)
    return ApiResponse.ok(result)


# ── 2.9. 사용자 비활성화 (ADMIN 전용) ──
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role(Role.ADMIN, Role.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """사용자 비활성화 (ADMIN 전용)"""
    service = UserService(db)
    await service.deactivate_user(current_user, user_id)
