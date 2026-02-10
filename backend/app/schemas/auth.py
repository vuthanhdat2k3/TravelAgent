from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None  # Only if rotating refresh token
    token_type: str = "bearer"
    expires_in: int | None = None