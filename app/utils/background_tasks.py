import asyncio
import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.settings import Settings
from app.bot.manager import get_bot_status
from app.utils.panel_status import get_panel_status
from app.utils.discord_webhook import DiscordWebhook

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/background_tasks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("background_tasks")

async def send_status_update():
    """
    Send a status update to Discord
    """
    try:
        # Get a database session
        db = SessionLocal()

        try:
            # Get the settings
            settings = db.query(Settings).first()

            if not settings or not settings.webhook_url:
                logger.warning("No webhook URL configured")
                return

            # Get the bot and panel status
            bot_status = get_bot_status(settings.bot_entrypoint)
            panel_status = get_panel_status()

            # Send the webhook
            webhook = DiscordWebhook(settings.webhook_url)
            message_id = webhook.send_status_update(bot_status, panel_status, settings.webhook_message_id)

            if message_id:
                # Update the message ID in the database
                settings.webhook_message_id = message_id
                db.commit()
                logger.info(f"Status update sent successfully (Message ID: {message_id})")
            else:
                logger.warning("Failed to send status update")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error sending status update: {e}")

async def status_update_task():
    """
    Background task to send status updates every minute
    """
    logger.info("Starting status update background task")

    # Send an initial status update
    await send_status_update()

    # Send status updates every minute
    while True:
        try:
            await asyncio.sleep(60)  # Wait for 1 minute
            await send_status_update()
        except Exception as e:
            logger.error(f"Error in status update task: {e}")
            await asyncio.sleep(10)  # Wait a bit before retrying
