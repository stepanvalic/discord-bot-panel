import asyncio
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.db.session import SessionLocal
from app.models.settings import Settings
from app.utils.discord_avatar import update_all_avatars

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)

# Configure logger
logger = logging.getLogger("avatar_background_task")
logger.setLevel(logging.INFO)

# Create a file handler for the avatar logs
file_handler = logging.FileHandler("logs/avatar_update.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

async def update_avatars_task():
    """
    Background task to update Discord avatars periodically
    """
    logger.info("Starting Discord avatar update background task")

    # Run an initial update
    try:
        logger.info("Running initial avatar update")
        # Force the initial update
        update_all_avatars(force=True)
    except Exception as e:
        logger.error(f"Error in initial avatar update: {e}")

    # Run periodic updates
    while True:
        try:
            # Get the update interval from settings
            db = SessionLocal()
            try:
                settings = db.query(Settings).first()

                if not settings or not settings.discord_bot_token:
                    # No token configured, wait for a shorter time
                    logger.warning("No Discord bot token configured, waiting 10 minutes before checking again")
                    await asyncio.sleep(600)  # 10 minutes
                    continue

                # Get the interval (default: 60 minutes)
                interval_minutes = settings.avatar_update_interval or 60

                # Get the last update time
                last_update = settings.last_avatar_update

                # Calculate next update time
                if last_update:
                    next_update = last_update + timedelta(minutes=interval_minutes)
                    now = datetime.now()

                    if next_update > now:
                        # Not time to update yet
                        wait_seconds = (next_update - now).total_seconds()
                        logger.info(f"Next avatar update scheduled at {next_update.isoformat()}, waiting {wait_seconds:.0f} seconds")
                        await asyncio.sleep(wait_seconds)
                    else:
                        # Time to update
                        logger.info(f"Running scheduled avatar update (interval: {interval_minutes} minutes)")
                        # No need to force here, it's already time for the update
                        update_all_avatars(force=False)

                        # Wait for the next interval
                        await asyncio.sleep(interval_minutes * 60)
                else:
                    # No last update time, run update now
                    logger.info(f"No previous update time found, running avatar update now")
                    # Force update since there's no previous update time
                    update_all_avatars(force=True)

                    # Wait for the next interval
                    await asyncio.sleep(interval_minutes * 60)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in avatar update task: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(300)  # 5 minutes
