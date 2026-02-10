"""
Google Calendar OAuth integration routes.
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["google-calendar"])

# Google OAuth configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']

# These will be loaded from environment variables
GOOGLE_CLIENT_ID = getattr(settings, 'GOOGLE_CLIENT_ID', None)
GOOGLE_CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
GOOGLE_REDIRECT_URI = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/google-calendar/callback')


@router.get("/google-calendar/auth/url")
async def get_google_auth_url(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get Google OAuth authorization URL for Calendar access.
    User should be redirected to this URL to grant permissions.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Calendar OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=str(current_user.id)  # Encode user_id in state for callback
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "user_id": str(current_user.id)
        }
    
    except Exception as e:
        logger.error(f"Failed to generate Google auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/google-calendar/callback")
async def google_calendar_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth callback endpoint. Exchanges authorization code for tokens.
    Note: This endpoint does NOT require authentication because Google redirects here.
    User identification is handled via session cookies or state parameter.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Calendar OAuth is not configured."
        )
    
    try:
        # Extract user_id from state parameter (we encoded it in get_google_auth_url)
        try:
            user_id = UUID(state)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter. Please restart OAuth flow."
            )
        
        # Get user from database
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,  # Use same scopes as auth URL generation
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save tokens to user metadata
        google_tokens = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        # Update user metadata
        metadata = user.metadata_ or {}
        metadata['google_calendar'] = google_tokens
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(metadata_=metadata)
        )
        await db.commit()
        
        logger.info(f"Successfully connected Google Calendar for user {user_id}")
        
        # Redirect to frontend success page
        return {
            "success": True,
            "message": "Google Calendar connected successfully",
            "user_email": user.email
        }
    
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Google Calendar: {str(e)}"
        )


@router.get("/google-calendar/status")
async def get_google_calendar_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Check if user has connected Google Calendar.
    """
    google_tokens = current_user.metadata_.get('google_calendar', {}) if current_user.metadata_ else {}
    
    is_connected = bool(google_tokens.get('access_token') and google_tokens.get('refresh_token'))
    
    return {
        "connected": is_connected,
        "email": google_tokens.get('email') if is_connected else None
    }


@router.delete("/google-calendar/disconnect")
async def disconnect_google_calendar(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect Google Calendar by removing stored tokens.
    """
    metadata = current_user.metadata_ or {}
    
    if 'google_calendar' in metadata:
        del metadata['google_calendar']
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(metadata_=metadata)
        )
        await db.commit()
        
        logger.info(f"Disconnected Google Calendar for user {current_user.id}")
    
    return {
        "success": True,
        "message": "Google Calendar disconnected"
    }
