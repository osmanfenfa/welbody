"""
User API endpoints for user management
Only ADMIN users can create, update, and delete other users
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
from typing import Optional

from app.core.dependencies import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from app.models.user import User
from app.utils.auth_utils import decode_token

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(authorization: Optional[str] = Header(None), x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None)):
    """Resolve the current user from `Authorization: Bearer <token>` header
    or fallback to `X-User-Id` + `X-User-Role` headers for convenience.
    Returns a dict: {"user_id": ..., "role": ...}
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        return decode_token(token)

    # fallback (legacy/testing): allow X-User-Id and X-User-Role
    if x_user_id and x_user_role:
        return {"user_id": x_user_id, "role": x_user_role}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication headers")


def verify_admin_role(current_user: dict = Depends(get_current_user)):
    role = (current_user.get("role") or "").upper()
    if role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN users can perform this action")
    return current_user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin_role: str = Depends(verify_admin_role)
):
    """
    Create a new user (ADMIN ONLY)
    
    Only users with ADMIN role can create new users for the system.
    Pass X-User-Role: ADMIN header to authorize this action.
    
    Request body:
    - username: Unique username (required)
    - email: User's email (optional)
    - full_name: User's full name (optional)
    - role: User's role - one of: DOCTOR, NURSE, PHARMACIST, LAB_TECHNICIAN, TRIAGE (optional)
    
    Required headers:
    - X-User-Role: ADMIN
    """
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Create new user
        new_user = User(
            user_id=f"USR-{uuid4().hex[:8].upper()}",
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination
    
    Query parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        total = db.query(User).count()
        return {
            "users": users,
            "total": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific user by user_id
    
    Path parameters:
    - user_id: The unique user identifier (e.g., USR-xxx)
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin_role: str = Depends(verify_admin_role)
):
    """
    Update a user (ADMIN ONLY)
    
    Only ADMIN users can modify other users' information.
    Pass X-User-Role: ADMIN header to authorize this action.
    
    Path parameters:
    - user_id: The unique user identifier
    
    Request body:
    - email: User's email (optional)
    - full_name: User's full name (optional)
    - role: User's role (optional)
    - is_active: Whether user is active (optional)
    
    Required headers:
    - X-User-Role: ADMIN
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        db.commit()
        db.refresh(user)
        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_role: str = Depends(verify_admin_role)
):
    """
    Delete a user (ADMIN ONLY)
    
    Only ADMIN users can delete users from the system.
    Pass X-User-Role: ADMIN header to authorize this action.
    
    Path parameters:
    - user_id: The unique user identifier
    
    Required headers:
    - X-User-Role: ADMIN
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db.delete(user)
        db.commit()
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
