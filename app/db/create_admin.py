
from getpass import getpass

from app.db.database import SessionLocal
from app.models import User
from app.core.security import hash_password


def create_admin():
    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()
    password = getpass("Enter admin password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if user:
            user.full_name = name
            user.password_hash = hash_password(password)
            user.role = "SUPER_ADMIN"
            user.user_type = "EMPLOYEE"
            user.is_active = True
            user.is_verified = True
            print("Existing account updated as SUPER_ADMIN.")
        else:
            user = User(
                full_name=name,
                email=email,
                password_hash=hash_password(password),
                role="SUPER_ADMIN",
                user_type="EMPLOYEE",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            print("SUPER_ADMIN account created.")

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
