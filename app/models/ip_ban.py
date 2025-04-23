from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class IPBan(Base):
    """
    IP Ban model for storing banned IP addresses
    """
    __tablename__ = "ip_bans"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True, nullable=False)
    failed_attempts = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    banned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
