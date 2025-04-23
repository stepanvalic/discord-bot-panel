from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
import hmac
import hashlib
import subprocess
import os
import logging
import json

from app.db.session import get_db
from app.models.settings import Settings
from app.bot.manager import restart_bot, install_bot_requirements

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook")

webhook_router = APIRouter()


@webhook_router.post("/receive")
async def receive_webhook(
    request: Request,
    x_hub_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Receive a webhook from GitHub

    Supports special commands in commit messages:
    - "--restart": Restarts the bot after pulling changes
    - "--piprestart": Installs requirements and then restarts the bot
    """
    # Get the settings
    settings = db.query(Settings).first()

    if not settings or not settings.webhook_key:
        raise HTTPException(status_code=404, detail="Webhook not configured")

    # Get the request body
    body = await request.body()

    # Verify the signature
    if x_hub_signature:
        # Calculate the expected signature
        signature = hmac.new(
            settings.webhook_key.encode(),
            body,
            hashlib.sha1
        ).hexdigest()
        expected_signature = f"sha1={signature}"

        # Compare signatures
        if not hmac.compare_digest(expected_signature, x_hub_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        # Parse the webhook payload
        payload = json.loads(body)

        # Check for special commands in commit messages
        special_command = None
        if "commits" in payload and len(payload["commits"]) > 0:
            # Get the most recent commit message
            commit_message = payload["commits"][0].get("message", "")
            logger.info(f"Received webhook with commit message: {commit_message}")

            # Check for special commands
            if "--piprestart" in commit_message:
                special_command = "piprestart"
                logger.info("Detected --piprestart command in commit message")
            elif "--restart" in commit_message:
                special_command = "restart"
                logger.info("Detected --restart command in commit message")

        # Pull the latest changes
        work_dir = "work-bot"

        # Ensure the work directory exists
        os.makedirs(work_dir, exist_ok=True)

        # Check if the directory is a git repository
        if os.path.exists(os.path.join(work_dir, ".git")):
            # Pull the latest changes
            subprocess.run(
                ["git", "pull"],
                cwd=work_dir,
                check=True
            )
            logger.info("Git pull successful")
        else:
            logger.warning("Not a git repository")
            return {"status": "error", "message": "Not a git repository"}

        # Handle special commands
        if special_command == "piprestart":
            # Install requirements
            logger.info("Installing requirements due to --piprestart command")
            success, message, _ = install_bot_requirements()
            if not success:
                logger.error(f"Failed to install requirements: {message}")
                return {"status": "error", "message": f"Failed to install requirements: {message}"}

            # Restart the bot
            restart_bot(settings.bot_entrypoint)
            logger.info("Bot restarted after installing requirements")
            return {"status": "success", "message": "Requirements installed and bot restarted"}
        elif special_command == "restart":
            # Just restart the bot
            restart_bot(settings.bot_entrypoint)
            logger.info("Bot restarted due to --restart command")
            return {"status": "success", "message": "Bot restarted"}
        else:
            # Default behavior - restart the bot
            restart_bot(settings.bot_entrypoint)
            logger.info("Bot restarted after webhook (default behavior)")

            return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}
