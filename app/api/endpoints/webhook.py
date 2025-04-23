from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import os
import secrets

from app.utils.key_generator import generate_complex_key

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.schemas.webhook import WebhookInfo, WebhookUpdate

router = APIRouter()


@router.get("", response_model=WebhookInfo)
async def get_webhook_info(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current webhook info
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {
        "url": settings.webhook_url,
        "key": settings.webhook_key,
        "message_id": settings.webhook_message_id
    }


@router.post("", response_model=WebhookInfo)
async def update_webhook_url(
    webhook_data: WebhookUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Update the webhook URL
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update the webhook URL and message ID
    settings.webhook_url = webhook_data.url
    settings.webhook_message_id = webhook_data.message_id
    db.commit()

    return {
        "url": settings.webhook_url,
        "key": settings.webhook_key,
        "message_id": settings.webhook_message_id
    }


@router.post("/regenerate", response_model=WebhookInfo)
async def regenerate_webhook_key(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Regenerate the webhook key
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Generate a new webhook key with 32 characters including uppercase, lowercase, and digits
    settings.webhook_key = generate_complex_key(32)
    db.commit()

    return {
        "url": settings.webhook_url,
        "key": settings.webhook_key,
        "message_id": settings.webhook_message_id
    }