from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from services.auth import Auth, UserAuthData, get_admin, get_auth, get_user, HashHelper
from sqlmodel import Session, select
from data.models.user import User
from data.database import get_db
from typing import Sequence
import re

user_router = APIRouter(prefix="/user")


class LoginPayload(BaseModel):
    username_or_email: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "username_or_email": "user@example.com",
                "password": "Password123!",
            }
        }


@user_router.get("/", response_model=Sequence[User])
def get_users(
    sesh: Session = Depends(get_db), admin: User = Depends(get_admin)
) -> Sequence[User]:
    """
    Get a list of all users.

    Args:
        sesh (Session): Database session.
        admin (User): Admin user.

    Returns:
        Sequence[User]: List of users.
    """
    return sesh.exec(select(User)).all()


@user_router.post("/login", response_model=str)
def login(
    loginPayload: LoginPayload,
    auth: Auth = Depends(get_auth),
    sesh: Session = Depends(get_db),
) -> str:
    """
    Authenticate a user and return a token.

    Args:
        loginPayload (LoginPayload): Login payload containing username or email and password.
        auth (Auth): Authentication service.
        sesh (Session): Database session.

    Returns:
        str: Authentication token.
    """
    user = sesh.exec(
        select(User).where(
            (User.username == loginPayload.username_or_email)
            | (User.email == loginPayload.username_or_email)
        )
    ).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if HashHelper.verify(loginPayload.password, user.password_hash) is False:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.id is None:
        raise HTTPException(status_code=404, detail="User ID is missing")

    user_data = UserAuthData(username=user.username, user_id=user.id)

    token = auth.create_token(user_data, False)

    return token


class NewUserPayload(BaseModel):
    username: str
    email: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
            }
        }


@user_router.post("/create")
def create_user(
    new_user_data: NewUserPayload,
    sesh: Session = Depends(get_db),
):
    """
    Create a new user.

    Args:
        new_user_data (NewUserPayload): New user data containing username, email, and password.
        sesh (Session): Database session.
    """
    errors = []
    if (
        sesh.exec(select(User).where(User.username == new_user_data.username)).first()
        is not None
    ):
        errors.append("Username already exists")

    if (
        sesh.exec(select(User).where(User.email == new_user_data.email)).first()
        is not None
    ):
        errors.append("Email already exists")

    def is_valid_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    if not is_valid_email(new_user_data.email):
        errors.append("Invalid email. Email must be in the format of 1Dlq9@example.com")

    if is_valid_email(new_user_data.username):
        errors.append("Username cannot be an email address")

    def is_valid_username(username: str) -> bool:
        username_pattern = r"^[a-zA-Z0-9_]{3,20}$"
        return bool(re.match(username_pattern, username))

    if not is_valid_username(new_user_data.username):
        errors.append(
            "Invalid username. Username must be between 3 and 20 characters and can only contain letters, numbers, and underscores."
        )

    def is_valid_password(password: str) -> list[str]:
        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            issues.append("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).'
            )

        return issues

    errors = errors + is_valid_password(new_user_data.password)

    if len(errors) > 0:
        raise HTTPException(status_code=400, detail=errors)

    user = User(
        username=new_user_data.username,
        email=new_user_data.email,
        password_hash=HashHelper.hash(new_user_data.password),
    )

    sesh.add(user)
    sesh.commit()


@user_router.post("/{user_name}/admin")
def upgrade_user(
    user_name: str, sesh: Session = Depends(get_db), admin: User = Depends(get_admin)
):
    """
    Upgrade a user to admin.

    Args:
        user_name (str): Username of the user to upgrade.
        sesh (Session): Database session.
        admin (User): Admin user.
    """
    user = sesh.exec(select(User).where(User.username == user_name)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.admin:
        raise HTTPException(status_code=400, detail="User is already admin")
    user.admin = True
    sesh.commit()


@user_router.delete("/{user_name}/admin")
def downgrade_user(
    user_name: str, sesh: Session = Depends(get_db), admin: User = Depends(get_admin)
):
    """
    Downgrade an admin user to a regular user.

    Args:
        user_name (str): Username of the user to downgrade.
        sesh (Session): Database session.
        admin (User): Admin user.
    """
    user = sesh.exec(select(User).where(User.username == user_name)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.admin is False:
        raise HTTPException(status_code=400, detail="User is not an admin")
    admins = sesh.exec(select(User).where(User.admin == True)).all()  # noqa: E712
    admin_count = len(admins)
    if admin_count == 1 and user.admin:
        raise HTTPException(status_code=400, detail="Can't downgrade the last admin")
    user.admin = False
    sesh.commit()


@user_router.delete("/delete")
async def delete_user(
    user_id: int = Query(None), user=Depends(get_user), db: Session = Depends(get_db)
):

    if user_id is None:
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}

    if user.id != user_id and not user.admin:
        raise HTTPException(
            status_code=403, detail="Unable to delete user with id " + str(user_id)
        )

    existing_user = db.get(User, user_id)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(existing_user)
    db.commit()

    return {"message": "User deleted successfully"}
