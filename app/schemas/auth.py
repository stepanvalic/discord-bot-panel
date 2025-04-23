from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """
    Token schema
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token data schema
    """
    username: Optional[str] = None


class UserBase(BaseModel):
    """
    Base user schema
    """
    username: str


class UserCreate(UserBase):
    """
    User creation schema
    """
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """
    User update schema
    """
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[str] = None
    discord_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserInDB(UserBase):
    """
    User in database schema
    """
    id: int
    role: str
    first_login: bool
    discord_id: Optional[str] = None
    avatar_url: Optional[str] = None
    discord_avatar_url: Optional[str] = None
    last_avatar_update: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """
    User response schema
    """
    id: int
    role: str
    discord_id: Optional[str] = None
    avatar_url: Optional[str] = None
    discord_avatar_url: Optional[str] = None
    last_avatar_update: Optional[datetime] = None

    class Config:
        from_attributes = True