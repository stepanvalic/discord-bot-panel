from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db.database import create_user, get_users, update_user, delete_user, is_db_initialized, get_user
from app.models.models import Token, UserCreate, UserResponse, UserUpdate

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, current_user: dict = Depends(get_current_admin_user)):
    # Check if user already exists
    existing_user = await get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    new_user = await create_user(user.username, hashed_password, user.role)

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        role=new_user["role"],
        created_at=new_user["created_at"]
    )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        role=current_user["role"],
        created_at=current_user["created_at"]
    )

@router.get("/initialized")
async def check_initialized():
    initialized = await is_db_initialized()
    return {"initialized": initialized}

@router.post("/setup", response_model=UserResponse)
async def setup_first_user(user: UserCreate):
    """Create the first admin user if no users exist."""
    # Check if database is already initialized
    initialized = await is_db_initialized()
    if initialized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database already initialized. Use the register endpoint to create new users."
        )

    # Check if user already exists
    existing_user = await get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password and create admin user
    hashed_password = get_password_hash(user.password)
    new_user = await create_user(user.username, hashed_password, "admin")

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        role=new_user["role"],
        created_at=new_user["created_at"]
    )
