from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, RefreshTokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.db.database import get_db
from app.services.user_service import (
    create_user,
    get_user_by_email,
    authenticate_user,
)
from app.core.auth import create_access_token, create_refresh_token
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])




@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = await create_user(db, user_create)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token."""
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    from app.core.auth import verify_refresh_token
    from app.services.user_service import get_user_by_id
    
    # Verify refresh token
    user_id_str = verify_refresh_token(refresh_data.refresh_token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    from uuid import UUID
    user_id = UUID(user_id_str)
    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Generate new access token
    new_access_token = create_access_token(subject=str(user.id))
    
    # Optionally rotate refresh token (generate new one)
    # Set to None if you don't want to rotate
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,  # Rotate refresh token for security
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """Logout current user."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)
