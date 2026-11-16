
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from app.db.database import Base


class TokenSession(Base):
    __tablename__ = "token_sessions"

    id = Column(Integer, primary_key=True, index=True)

    jti = Column(String(36), unique=True, nullable=False, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_type = Column(String(20), nullable=False)

    expires_at = Column(DateTime, nullable=False)

    revoked_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
