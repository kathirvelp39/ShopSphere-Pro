
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Address
from app.schemas.catalog import AddressCreate
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/addresses", tags=["Address Management"])


@router.post("/")
def create_address(
    data: AddressCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.address_type not in {"BILLING", "SHIPPING"}:
        raise HTTPException(400, "Address type must be BILLING or SHIPPING")

    if data.is_default:
        db.query(Address).filter(
            Address.user_id == user.id,
            Address.address_type == data.address_type,
        ).update({"is_default": False})

    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.get("/")
def list_addresses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Address).filter(
        Address.user_id == user.id
    ).all()


@router.patch("/{address_id}")
def update_address(
    address_id: int,
    data: AddressCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user.id,
    ).first()

    if not address:
        raise HTTPException(404, "Address not found")

    if data.address_type not in {"BILLING", "SHIPPING"}:
        raise HTTPException(400, "Invalid address type")

    changes = data.model_dump()

    if changes["is_default"]:
        db.query(Address).filter(
            Address.user_id == user.id,
            Address.address_type == data.address_type,
        ).update({"is_default": False})

    for key, value in changes.items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user.id,
    ).first()

    if not address:
        raise HTTPException(404, "Address not found")

    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}
