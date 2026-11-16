
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(150), nullable=False)

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(String(255), nullable=False)

    role = Column(
        String(50),
        nullable=False,
        default="CUSTOMER",
    )

    user_type = Column(
        String(20),
        nullable=False,
        default="CUSTOMER",
    )

    is_active = Column(Boolean, default=True, nullable=False)

    is_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
