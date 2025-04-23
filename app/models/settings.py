from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Settings(Base):
    """
    Settings model for application configuration
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ssh_public_key = Column(String, nullable=True)
    ssh_private_key = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    webhook_key = Column(String, nullable=True)
    webhook_message_id = Column(String, nullable=True)
    bot_entrypoint = Column(String, default="bot.py")
    env_whitelist = Column(String, default=".env")
    bot_venv = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Discord bot settings
    discord_bot_token = Column(String, nullable=True)  # Token pro Discord bota
    avatar_update_interval = Column(Integer, default=60)  # Interval aktualizace avatarů v minutách (výchozí: 60 minut)
    last_avatar_update = Column(DateTime(timezone=True), nullable=True)  # Čas poslední aktualizace avatarů

    # Relationship
    user = relationship("User", backref="settings")
