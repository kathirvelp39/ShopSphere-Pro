
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.schemas.catalog import UserUpdate
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/users", tags=["User Management"])

ADMIN_ROLES = ("SUPER_ADMIN", "ADMIN")


@router.get("/")
def list_users(
    search: str | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(*ADMIN_ROLES)),
):
    query = db.query(User)

    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%")
            | User.email.ilike(f"%{search}%")
        )

    if role:
        query = query.filter(User.role == role.upper())

    return query.order_by(User.id.desc()).all()


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(*ADMIN_ROLES)),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    changes = data.model_dump(exclude_unset=True)

    if "role" in changes:
        allowed = {
            "SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER",
            "INVENTORY_MANAGER", "ORDER_MANAGER",
            "SUPPORT_AGENT", "CUSTOMER", "DELIVERY_MANAGER",
            "FINANCE_MANAGER",
        }
        if changes["role"] not in allowed:
            raise HTTPException(400, "Invalid role")

    for key, value in changes.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(*ADMIN_ROLES)),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.id == admin.id:
        raise HTTPException(400, "You cannot deactivate your own account")

    user.is_active = False
    db.commit()

    return {"message": "User deactivated successfully"}
