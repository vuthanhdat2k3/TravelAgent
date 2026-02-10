"""FastAPI dependencies for authentication and authorization."""

from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.auth import verify_password
from app.db.database import get_db
from app.services.user_service import get_user_by_id

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Extract user ID from JWT token."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.APP_JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return UUID(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user."""
    from app.services.user_service import get_current_user as get_user
    return await get_user(db, user_id)


async def get_current_active_user(
    current_user = Depends(get_current_user),
):
    """Get current active user (must be active)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_active_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
):
    """Get current active user if authenticated, otherwise None."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.APP_JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = UUID(user_id_str)
        user = await get_user_by_id(db, user_id)
        
        if user and user.is_active:
            return user
        return None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


async def get_current_superuser(
    current_user = Depends(get_current_active_user),
):
    """Get current superuser (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
