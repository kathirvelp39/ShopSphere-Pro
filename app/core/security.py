
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

password_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password before saving it to the database."""
    return password_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Compare a login password with its stored hash."""
    return password_context.verify(plain_password, hashed_password)


def create_token(
    user_id: int,
    token_type: str,
    expires_delta: timedelta,
) -> dict:
    """Create a signed JWT with a unique token ID."""
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid4())

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    encoded_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "token": encoded_token,
        "jti": jti,
        "expires_at": expires_at.replace(tzinfo=None),
    }


def decode_token(token: str) -> dict:
    """Decode and verify a JWT."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
    )
