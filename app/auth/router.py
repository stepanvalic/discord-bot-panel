from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserResponse, UserUpdate
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_random_password,
)
from app.auth.dependencies import get_current_user_from_session, get_current_admin_from_session

auth_router = APIRouter()


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate the user
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # If this is the first login, mark it as completed
    if user.first_login:
        user.first_login = False
        db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (only available if no users exist)
    """
    # Check if any users exist
    user_count = db.query(User).count()

    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Please contact an administrator.",
        )

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user with admin role (first user)
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role="admin",
        first_login=False,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@auth_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Create a new user (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role="user",
        first_login=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@auth_router.get("/users", response_model=list[UserResponse])
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Get all users (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    users = db.query(User).all()
    return users


@auth_router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get current user info
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


@auth_router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Update current user
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Update password if provided
    if user_data.password:
        current_user.password_hash = get_password_hash(user_data.password)
        current_user.first_login = False

    db.commit()
    db.refresh(current_user)

    return current_user


@auth_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Update a user (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password if provided
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
        user.first_login = True

    # Update role if provided
    if user_data.role:
        user.role = user_data.role

    # Update Discord ID if provided (even if it's an empty string)
    if user_data.discord_id is not None:
        # Check if another user already has this Discord ID
        if user_data.discord_id:
            existing_user = db.query(User).filter(User.discord_id == user_data.discord_id, User.id != user_id).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This Discord ID is already in use by another user",
                )
        user.discord_id = user_data.discord_id if user_data.discord_id else None

    db.commit()
    db.refresh(user)

    return user


@auth_router.post("/users/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Reset a user's password (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate a new random password
    new_password = generate_random_password()

    # Update the user's password
    user.password_hash = get_password_hash(new_password)
    user.first_login = True

    db.commit()

    return {"password": new_password}


@auth_router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """
    Delete a user (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    # Get the user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete the user
    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
