from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.core.security import ROLE_PERMISSIONS, STAFF_ROLES, SYSTEM_ROLES, normalize_role
from app.models.user import User
from app.schemas.admin import (
    AdminLoginRequest,
    AdminSignupRequest,
    AdminUserCreateRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
    AuditLogListResponse,
    AuthResponse,
    RoleAssignmentRequest,
    RolePermissionsResponse,
)
from app.services.audit_service import AuditService
from app.utils.auth_utils import encode_token, hash_password, verify_password

router = APIRouter(prefix="/admin", tags=["admin"])


def _resolve_username(db: Session, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    db_user = db.query(User).filter(User.user_id == user_id).first()
    return db_user.username if db_user else None


def _permissions_for_role(role: Optional[str]) -> list[str]:
    return ROLE_PERMISSIONS.get(normalize_role(role), [])


def _validate_staff_role(role: str) -> str:
    normalized = normalize_role(role)
    if normalized not in STAFF_ROLES:
        allowed = ", ".join(sorted(STAFF_ROLES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid staff role. Allowed roles: {allowed}",
        )
    return normalized


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def admin_signup(payload: AdminSignupRequest, db: Session = Depends(get_db)):
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_admin = db.query(User).filter(User.role.ilike("ADMIN")).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin signup is closed. Use an existing admin account.",
        )

    new_admin = User(
        user_id=f"USR-{uuid4().hex[:8].upper()}",
        username=payload.username,
        hashed_password=hash_password(payload.password),
        email=payload.email,
        full_name=payload.full_name,
        role="ADMIN",
        is_active=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    token = encode_token(new_admin.user_id, "ADMIN")
    AuditService.log_event(
        db=db,
        event_type="ADMIN_SIGNUP",
        user_id=new_admin.user_id,
        username=new_admin.username,
        endpoint="/admin/signup",
        method="POST",
        details="Initial admin account created",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_admin.user_id,
        "username": new_admin.username,
        "role": "ADMIN",
        "permissions": _permissions_for_role("ADMIN"),
    }


@router.post("/login", response_model=AuthResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == payload.username).first()
    if not admin or normalize_role(admin.role) != "ADMIN" or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, admin.hashed_password or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = encode_token(admin.user_id, "ADMIN")
    AuditService.log_event(
        db=db,
        event_type="ADMIN_LOGIN",
        user_id=admin.user_id,
        username=admin.username,
        endpoint="/admin/login",
        method="POST",
        details="Admin logged in",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": admin.user_id,
        "username": admin.username,
        "role": "ADMIN",
        "permissions": _permissions_for_role("ADMIN"),
    }


@router.get("/roles/permissions", response_model=RolePermissionsResponse)
def get_role_permissions(current_user: dict = Depends(require_admin)):
    return {"roles": ROLE_PERMISSIONS}


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    query = db.query(User)
    if role:
        normalized_role = normalize_role(role)
        if normalized_role not in SYSTEM_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role filter")
        query = query.filter(User.role == normalized_role)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return {"users": users, "total": total}


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    role = _validate_staff_role(payload.role)
    new_user = User(
        user_id=f"USR-{uuid4().hex[:8].upper()}",
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=role,
        email=payload.email,
        full_name=payload.full_name,
        is_active=payload.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    admin_username = _resolve_username(db, current_user.get("user_id"))
    AuditService.log_event(
        db=db,
        event_type="USER_CREATED",
        user_id=current_user.get("user_id"),
        username=admin_username,
        endpoint="/admin/users",
        method="POST",
        details=f"Created user {new_user.user_id} with role {role}",
    )
    return new_user


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role is not None:
        user.role = _validate_staff_role(payload.role)
    if payload.email is not None:
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    admin_username = _resolve_username(db, current_user.get("user_id"))
    AuditService.log_event(
        db=db,
        event_type="USER_UPDATED",
        user_id=current_user.get("user_id"),
        username=admin_username,
        endpoint=f"/admin/users/{user_id}",
        method="PUT",
        details=f"Updated user {user.user_id}",
    )
    return user


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
def assign_role(
    user_id: str,
    payload: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_role = _validate_staff_role(payload.role)
    user.role = new_role
    db.commit()
    db.refresh(user)

    admin_username = _resolve_username(db, current_user.get("user_id"))
    AuditService.log_event(
        db=db,
        event_type="USER_ROLE_UPDATED",
        user_id=current_user.get("user_id"),
        username=admin_username,
        endpoint=f"/admin/users/{user_id}/role",
        method="PUT",
        details=f"Assigned role {new_role} to {user.user_id}",
    )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    if current_user.get("user_id") == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()

    admin_username = _resolve_username(db, current_user.get("user_id"))
    AuditService.log_event(
        db=db,
        event_type="USER_DELETED",
        user_id=current_user.get("user_id"),
        username=admin_username,
        endpoint=f"/admin/users/{user_id}",
        method="DELETE",
        details=f"Deleted user {user_id}",
    )
    return None


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    total, logs = AuditService.list_logs(
        db=db,
        skip=skip,
        limit=limit,
        event_type=event_type,
        user_id=user_id,
    )
    return {"logs": logs, "total": total}
