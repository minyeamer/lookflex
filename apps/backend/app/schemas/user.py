"""User 도메인 Pydantic 스키마"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

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
