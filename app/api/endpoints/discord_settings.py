import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session, get_current_admin_from_session
from app.utils.discord_avatar import update_all_avatars

router = APIRouter()

class DiscordBotSettings(BaseModel):
    """
    Discord bot settings schema
    """
    discord_bot_token: Optional[str] = None
    avatar_update_interval: Optional[int] = None

@router.get("/settings", response_model=DiscordBotSettings)
async def get_discord_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Get Discord bot settings (admin only)
    """
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {
        "discord_bot_token": settings.discord_bot_token or "",
        "avatar_update_interval": settings.avatar_update_interval or 60
    }

@router.put("/settings", response_model=DiscordBotSettings)
async def update_discord_settings(
    settings_data: DiscordBotSettings,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Update Discord bot settings (admin only)
    """
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update settings
    if settings_data.discord_bot_token is not None:
        settings.discord_bot_token = settings_data.discord_bot_token

    if settings_data.avatar_update_interval is not None:
        settings.avatar_update_interval = settings_data.avatar_update_interval

    db.commit()

    return {
        "discord_bot_token": settings.discord_bot_token or "",
        "avatar_update_interval": settings.avatar_update_interval or 60
    }

@router.post("/update-avatars")
async def trigger_avatar_update(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Trigger an immediate update of all Discord avatars (admin only)
    """
    try:
        # Force update regardless of the last update time
        result = update_all_avatars(force=True)
        if result:
            return {"status": "success", "message": "Avatar update completed successfully"}
        else:
            return {"status": "warning", "message": "Avatar update failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating avatars: {str(e)}")


@router.get("/logs")
async def get_avatar_logs(
    request: Request,
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Get the avatar update logs (admin only)
    """
    try:
        # Path to the log file
        log_file_path = "logs/avatar_update.log"

        # Check if the log file exists
        if not os.path.exists(log_file_path):
            return {"logs": ["No log file found. Avatar updates may not have run yet."]}

        # Read the log file (last 100 lines)
        with open(log_file_path, "r") as f:
            # Read all lines and get the last 100
            lines = f.readlines()
            logs = lines[-100:] if len(lines) > 100 else lines

        return {"logs": logs}
    except Exception as e:
        logging.error(f"Error reading avatar logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")
