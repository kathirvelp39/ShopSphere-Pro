
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User, CustomerProfile, ProfileHistory
from app.schemas.catalog import CustomerProfileUpdate
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/customers", tags=["Customer Profiles"])


@router.get("/me")
def get_profile(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CustomerProfile).filter(
        CustomerProfile.user_id == user.id
    ).first()

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": profile.phone_number if profile else None,
        "is_email_verified": profile.is_email_verified if profile else False,
    }


@router.patch("/me")
def update_profile(
    data: CustomerProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.user_type != "CUSTOMER":
        raise HTTPException(403, "Customer account required")

    profile = db.query(CustomerProfile).filter(
        CustomerProfile.user_id == user.id
    ).first()

    if not profile:
        profile = CustomerProfile(user_id=user.id)
        db.add(profile)

    if data.full_name is not None and data.full_name != user.full_name:
        db.add(ProfileHistory(
            user_id=user.id,
            field_name="full_name",
            old_value=user.full_name,
            new_value=data.full_name,
        ))
        user.full_name = data.full_name

    if data.phone_number is not None and data.phone_number != profile.phone_number:
        db.add(ProfileHistory(
            user_id=user.id,
            field_name="phone_number",
            old_value=profile.phone_number,
            new_value=data.phone_number,
        ))
        profile.phone_number = data.phone_number

    db.commit()
    return {"message": "Profile updated successfully"}


@router.post("/me/deactivate")
def deactivate_my_account(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.is_active = False
    db.commit()
    return {"message": "Account deactivated successfully"}


@router.post("/verify-email")
def verify_email(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CustomerProfile).filter(
        CustomerProfile.user_id == user.id
    ).first()

    if not profile:
        profile = CustomerProfile(
            user_id=user.id,
            verification_token=secrets.token_urlsafe(32),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    if profile.is_email_verified:
        return {"message": "Email already verified"}

    return {
        "message": "Verification token generated. Configure an email provider to deliver it.",
        "verification_token": profile.verification_token,
    }


@router.post("/verify-email/confirm")
def confirm_email(
    token: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CustomerProfile).filter(
        CustomerProfile.user_id == user.id,
        CustomerProfile.verification_token == token,
    ).first()

    if not profile:
        raise HTTPException(400, "Invalid verification token")

    profile.is_email_verified = True
    profile.verification_token = None
    db.commit()

    return {"message": "Email verified successfully"}
