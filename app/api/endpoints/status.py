from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.bot.manager import get_bot_status
from app.utils.panel_status import get_panel_status
from app.utils.discord_webhook import DiscordWebhook

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/status.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("status")

router = APIRouter()

# Store the last message ID
LAST_MESSAGE_ID = None


@router.get("/panel")
async def panel_status(
    request: Optional[Dict[str, Any]] = None,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current status of the panel
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the panel status
    status = get_panel_status()

    return status


@router.post("/webhook")
async def send_webhook_status(
    background_tasks: BackgroundTasks,
    request: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Send a status update to the Discord webhook
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the settings
    settings = db.query(Settings).first()

    if not settings or not settings.webhook_url:
        raise HTTPException(status_code=404, detail="Webhook URL not configured")

    # Get the bot and panel status
    bot_status = get_bot_status(settings.bot_entrypoint)
    panel_status = get_panel_status()

    # Send the webhook in the background
    background_tasks.add_task(
        send_webhook_status_task,
        settings.webhook_url,
        bot_status,
        panel_status,
        settings.webhook_message_id,
        db
    )

    return {"status": "Webhook status update queued"}


async def send_webhook_status_task(webhook_url: str, bot_status: Dict[str, Any], panel_status: Dict[str, Any], message_id: Optional[str], db: Session):
    """
    Background task to send webhook status
    """
    try:
        webhook = DiscordWebhook(webhook_url)
        new_message_id = webhook.send_status_update(bot_status, panel_status, message_id)

        if new_message_id:
            # Update the message ID in the database
            settings = db.query(Settings).first()
            if settings:
                settings.webhook_message_id = new_message_id
                db.commit()
    except Exception as e:
        logger.error(f"Error in webhook status task: {e}")
