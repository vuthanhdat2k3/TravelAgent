from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
import bcrypt
from app.core.config import settings

# Bcrypt only supports passwords up to 72 bytes
# We hash passwords with SHA256 first if they're too long, otherwise use directly
# This ensures compatibility while preserving security for normal-length passwords
BCRYPT_MAX_PASSWORD_LENGTH = 72


def _prepare_password(password: str) -> bytes:
    """Prepare password for bcrypt. Hash with SHA256 if too long."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        # Hash with SHA256 to get fixed 32 bytes for long passwords
        password_bytes = hashlib.sha256(password_bytes).digest()
    return password_bytes


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = _prepare_password(password)
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hashed password."""
    password_bytes = _prepare_password(password)
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False

def create_access_token(subject: str) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=settings.APP_JWT_EXP_TIME)
    payload = {"sub": subject, "iat": now, "exp": exp}
    return jwt.encode(payload=payload, key=settings.APP_JWT_SECRET, algorithm="HS256")

def create_refresh_token(subject: str) -> str:
    """Create JWT refresh token."""
    now = datetime.utcnow()
    exp = now + timedelta(days=settings.APP_REFRESH_TOKEN_DAYS)
    payload = {"sub": subject, "type": "refresh", "iat": now, "exp": exp}
    return jwt.encode(payload=payload, key=settings.APP_JWT_SECRET, algorithm="HS256")


def verify_refresh_token(token: str) -> str | None:
    """Verify refresh token and return user_id (subject) if valid."""
    try:
        payload = jwt.decode(token, settings.APP_JWT_SECRET, algorithms=["HS256"])
        token_type = payload.get("type")
        if token_type != "refresh":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()