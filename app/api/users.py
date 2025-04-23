from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.auth.auth import get_current_admin_user, get_password_hash
from app.db.database import get_users, get_user, create_user, update_user, delete_user
from app.models.models import UserCreate, UserResponse, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(get_current_admin_user)):
    """List all users."""
    users = await get_users()
    
    return [
        UserResponse(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            created_at=user["created_at"]
        )
        for user in users
    ]

@router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate, current_user: dict = Depends(get_current_admin_user)):
    """Create a new user."""
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

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, current_user: dict = Depends(get_current_admin_user)):
    """Get a user by ID."""
    # Get all users
    users = await get_users()
    
    # Find the user with the given ID
    user = next((u for u in users if u["id"] == user_id), None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user["created_at"]
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(user_id: int, user_update: UserUpdate, current_user: dict = Depends(get_current_admin_user)):
    """Update a user by ID."""
    # Get all users
    users = await get_users()
    
    # Find the user with the given ID
    user = next((u for u in users if u["id"] == user_id), None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = {}
    
    if user_update.username is not None:
        # Check if username is already taken
        if user_update.username != user["username"]:
            existing_user = await get_user(user_update.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        update_data["username"] = user_update.username
    
    if user_update.password is not None:
        update_data["password_hash"] = get_password_hash(user_update.password)
    
    if user_update.role is not None:
        update_data["role"] = user_update.role
    
    # Update user
    updated_user = await update_user(user_id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return UserResponse(
        id=updated_user["id"],
        username=updated_user["username"],
        role=updated_user["role"],
        created_at=updated_user["created_at"]
    )

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user_by_id(user_id: int, current_user: dict = Depends(get_current_admin_user)):
    """Delete a user by ID."""
    # Get all users
    users = await get_users()
    
    # Find the user with the given ID
    user = next((u for u in users if u["id"] == user_id), None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting the last admin
    admin_users = [u for u in users if u["role"] == "admin"]
    if user["role"] == "admin" and len(admin_users) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last admin user"
        )
    
    # Delete user
    deleted_user = await delete_user(user_id)
    
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return UserResponse(
        id=deleted_user["id"],
        username=deleted_user["username"],
        role=deleted_user["role"],
        created_at=deleted_user["created_at"]
    )
