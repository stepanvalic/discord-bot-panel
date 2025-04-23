import os
import logging
from sqlalchemy.orm import Session
from app.utils.key_generator import generate_complex_key

from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.settings import Settings
from app.utils.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initialize the database with tables and default data
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Check if we need to create default settings
    if db.query(Settings).first() is None:
        logger.info("Creating default settings")
        default_settings = Settings(
            ssh_public_key="",
            ssh_private_key="",
            webhook_url="",
            webhook_key=generate_complex_key(32),
            bot_entrypoint="bot.py",
            env_whitelist=".env",
        )
        db.add(default_settings)
        db.commit()

    db.close()

    logger.info("Database initialized")


if __name__ == "__main__":
    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")
