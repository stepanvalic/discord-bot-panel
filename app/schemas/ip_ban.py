from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IPBanBase(BaseModel):
    """
    Base IP Ban schema
    """
    ip_address: str


class IPBanCreate(IPBanBase):
    """
    IP Ban creation schema
    """
    pass


class IPBanUpdate(BaseModel):
    """
    IP Ban update schema
    """
    failed_attempts: Optional[int] = None
    is_banned: Optional[bool] = None
    banned_at: Optional[datetime] = None


class IPBanInDB(IPBanBase):
    """
    IP Ban in database schema
    """
    id: int
    failed_attempts: int
    is_banned: bool
    banned_at: Optional[datetime] = None
    created_at: datetime
    last_attempt_at: datetime

    class Config:
        from_attributes = True


class IPBanResponse(IPBanBase):
    """
    IP Ban response schema
    """
    id: int
    failed_attempts: int
    is_banned: bool
    banned_at: Optional[datetime] = None
    created_at: datetime
    last_attempt_at: datetime

    class Config:
        from_attributes = True
