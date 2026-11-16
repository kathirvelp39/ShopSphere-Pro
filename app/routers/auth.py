
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, get_token_payload
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models import TokenSession, User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def issue_tokens(db: Session, user: User) -> TokenResponse:
    access = create_token(
        user.id,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = create_token(
        user.id,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add_all([
        TokenSession(
            jti=access["jti"],
            user_id=user.id,
            token_type="access",
            expires_at=access["expires_at"],
        ),
        TokenSession(
            jti=refresh["jti"],
            user_id=user.id,
            token_type="refresh",
            expires_at=refresh["expires_at"],
        ),
    ])
    db.commit()

    return TokenResponse(
        access_token=access["token"],
        refresh_token=refresh["token"],
    )


@router.post("/customer/register", response_model=MessageResponse)
def register_customer(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="CUSTOMER",
        user_type="CUSTOMER",
    )

    db.add(user)
    db.commit()

    return {"message": "Customer registered successfully"}


def authenticate_user(
    data: LoginRequest,
    user_type: str,
    db: Session,
):
    user = db.query(User).filter(
        User.email == data.email,
        User.user_type == user_type,
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return issue_tokens(db, user)


@router.post("/customer/login", response_model=TokenResponse)
def customer_login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    return authenticate_user(data, "CUSTOMER", db)


@router.post("/employee/login", response_model=TokenResponse)
def employee_login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    return authenticate_user(data, "EMPLOYEE", db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    old_session = db.query(TokenSession).filter(
        TokenSession.jti == payload.get("jti"),
        TokenSession.token_type == "refresh",
    ).first()

    if not old_session or old_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or is invalid",
        )

    user = db.query(User).filter(
        User.id == int(payload["sub"]),
        User.is_active.is_(True),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or does not exist",
        )

    old_session.revoked_at = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

    db.commit()

    return issue_tokens(db, user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    data: LogoutRequest,
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    access_session = db.query(TokenSession).filter(
        TokenSession.jti == payload.get("jti"),
        TokenSession.token_type == "access",
    ).first()

    if access_session and access_session.revoked_at is None:
        access_session.revoked_at = now

    if data.refresh_token:
        try:
            refresh_payload = decode_token(data.refresh_token)

            if (
                refresh_payload.get("type") == "refresh"
                and refresh_payload.get("sub") == payload.get("sub")
            ):
                refresh_session = db.query(TokenSession).filter(
                    TokenSession.jti == refresh_payload.get("jti"),
                    TokenSession.token_type == "refresh",
                ).first()

                if (
                    refresh_session
                    and refresh_session.revoked_at is None
                ):
                    refresh_session.revoked_at = now

        except JWTError:
            pass

    db.commit()

    return {"message": "Logged out successfully"}
