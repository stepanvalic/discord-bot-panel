from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    first_login = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    discord_id = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    discord_avatar_url = Column(String, nullable=True)  # URL avataru získaného z Discord API
    last_avatar_update = Column(DateTime(timezone=True), nullable=True)  # Čas poslední aktualizace avataru
