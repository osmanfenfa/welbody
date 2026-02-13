from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class AdminSignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    permissions: List[str]


class AdminUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = True


class AdminUserUpdateRequest(BaseModel):
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    is_active: Optional[bool] = None


class RoleAssignmentRequest(BaseModel):
    role: str


class AdminUserResponse(BaseModel):
    user_id: str
    username: str
    role: Optional[str]
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    total: int


class RolePermissionsResponse(BaseModel):
    roles: Dict[str, List[str]]


class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    user_id: Optional[str]
    username: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
