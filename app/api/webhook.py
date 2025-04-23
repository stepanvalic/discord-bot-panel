from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Dict

from app.auth.auth import get_current_active_user
from app.db.database import get_settings, update_settings, create_settings
from app.models.models import WebhookCreate, WebhookResponse, DiscordWebhookCreate, DiscordWebhookResponse
from app.utils.webhook import generate_webhook_key, verify_webhook_signature, process_github_webhook, process_gitlab_webhook
from app.utils.discord_webhook import send_discord_webhook, update_discord_webhook, create_panel_status_embed, create_bot_status_embed
from app.utils.ssh import git_pull_with_ssh
from app.bot.manager import restart_bot

router = APIRouter()

@router.get("/", response_model=WebhookResponse)
async def get_webhook(current_user: dict = Depends(get_current_active_user)):
    """Get the current webhook URL and key."""
    settings = await get_settings(current_user["id"])

    if not settings or not settings.get("webhook_url") or not settings.get("webhook_key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not configured"
        )

    return WebhookResponse(
        url=settings["webhook_url"],
        key=settings["webhook_key"]
    )

@router.post("/", response_model=WebhookResponse)
async def create_webhook(webhook: WebhookCreate, current_user: dict = Depends(get_current_active_user)):
    """Create or update the webhook URL."""
    # Generate a new webhook key if one doesn't exist
    settings = await get_settings(current_user["id"])

    if settings:
        # Get existing key or generate a new one
        webhook_key = settings.get("webhook_key") or generate_webhook_key()

        # Update settings
        updated_settings = await update_settings(
            current_user["id"],
            {"webhook_url": webhook.url, "webhook_key": webhook_key}
        )
    else:
        # Generate a new key
        webhook_key = generate_webhook_key()

        # Create new settings
        updated_settings = await create_settings(
            current_user["id"],
            webhook_url=webhook.url,
            webhook_key=webhook_key
        )

    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save webhook settings"
        )

    return WebhookResponse(
        url=updated_settings["webhook_url"],
        key=updated_settings["webhook_key"]
    )

@router.post("/regenerate", response_model=WebhookResponse)
async def regenerate_webhook_key(current_user: dict = Depends(get_current_active_user)):
    """Regenerate the webhook key."""
    settings = await get_settings(current_user["id"])

    if not settings or not settings.get("webhook_url"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not configured"
        )

    # Generate a new webhook key
    webhook_key = generate_webhook_key()

    # Update settings
    updated_settings = await update_settings(
        current_user["id"],
        {"webhook_key": webhook_key}
    )

    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate webhook key"
        )

    return WebhookResponse(
        url=updated_settings["webhook_url"],
        key=updated_settings["webhook_key"]
    )

@router.post("/receive")
async def receive_webhook(request: Request):
    """Receive and process a webhook."""
    # Get the request body
    payload_bytes = await request.body()
    payload = await request.json()

    # Get the signature from headers
    signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Gitlab-Token")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature"
        )

    # Get all settings to find the matching webhook key
    from app.db.database import get_users, get_settings
    users = await get_users()

    webhook_key = None
    ssh_private_key = None

    for user in users:
        user_settings = await get_settings(user["id"])
        if user_settings and user_settings.get("webhook_key"):
            # Verify the signature
            if verify_webhook_signature(payload_bytes, signature, user_settings["webhook_key"]):
                webhook_key = user_settings["webhook_key"]
                ssh_private_key = user_settings.get("ssh_private_key")
                break

    if not webhook_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    # Process the webhook based on the source
    if "repository" in payload:
        # GitHub webhook
        result = process_github_webhook(payload)
    elif "project" in payload:
        # GitLab webhook
        result = process_gitlab_webhook(payload)
    else:
        result = {"status": "error", "reason": "Unknown webhook format"}

    if result.get("status") != "success":
        return result

    # Pull changes if we have an SSH key
    if ssh_private_key:
        import os
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Get bot directory
        bot_dir = os.getenv("BOT_DIR", "./workspace")

        # Make sure we have an absolute path
        if not os.path.isabs(bot_dir):
            bot_dir = os.path.abspath(os.path.join(os.getcwd(), bot_dir.lstrip("./")))

        # Save SSH key to a temporary file
        from app.utils.ssh import save_ssh_key_to_file
        key_path = os.path.join(os.getcwd(), "temp_ssh_key")
        save_ssh_key_to_file(ssh_private_key, key_path)

        try:
            # Pull changes
            success, message = git_pull_with_ssh(bot_dir, key_path)

            if success:
                result["git_pull"] = "success"
                result["git_message"] = message

                # Restart the bot
                restart_result = restart_bot()
                result["bot_restart"] = restart_result.get("status")
            else:
                result["git_pull"] = "error"
                result["git_message"] = message
        finally:
            # Clean up temporary key file
            if os.path.exists(key_path):
                os.remove(key_path)

    return result

@router.get("/discord", response_model=DiscordWebhookResponse)
async def get_discord_webhook(current_user: dict = Depends(get_current_active_user)):
    """Get the current Discord webhook URLs."""
    settings = await get_settings(current_user["id"])

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord webhook not configured"
        )

    return DiscordWebhookResponse(
        panel_webhook_url=settings.get("discord_panel_webhook_url"),
        bot_webhook_url=settings.get("discord_bot_webhook_url"),
        message_id=settings.get("discord_webhook_message_id"),
        bot_message_id=settings.get("discord_bot_webhook_message_id")
    )

@router.post("/discord", response_model=DiscordWebhookResponse)
async def create_discord_webhook(webhook: DiscordWebhookCreate, current_user: dict = Depends(get_current_active_user)):
    """Create or update the Discord webhook URLs."""
    settings = await get_settings(current_user["id"])

    update_data = {}

    if webhook.panel_webhook_url is not None:
        update_data["discord_panel_webhook_url"] = webhook.panel_webhook_url

    if webhook.panel_message_id is not None:
        update_data["discord_webhook_message_id"] = webhook.panel_message_id

    if webhook.bot_webhook_url is not None:
        update_data["discord_bot_webhook_url"] = webhook.bot_webhook_url

    if webhook.bot_message_id is not None:
        update_data["discord_bot_webhook_message_id"] = webhook.bot_message_id

    if settings:
        # Update settings
        updated_settings = await update_settings(
            current_user["id"],
            update_data
        )
    else:
        # Create new settings
        updated_settings = await create_settings(
            current_user["id"],
            discord_panel_webhook_url=webhook.panel_webhook_url,
            discord_bot_webhook_url=webhook.bot_webhook_url
        )

    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save Discord webhook settings"
        )

    # Send initial status embeds
    message_id = None

    if webhook.panel_webhook_url:
        # Create combined panel and bot status embed
        panel_embed = create_panel_status_embed()

        # Check if we have a message ID for the panel webhook
        panel_message_id = webhook.panel_message_id or updated_settings.get("discord_webhook_message_id")

        if panel_message_id:
            # Update existing message
            success, error = await update_discord_webhook(
                webhook.panel_webhook_url,
                panel_message_id,
                panel_embed
            )

            if success:
                message_id = panel_message_id
                updated_settings["discord_webhook_message_id"] = message_id
            elif "Unknown Message" in (error or ""):
                # Message was deleted, send a new one
                success, new_message_id, error = await send_discord_webhook(
                    webhook.panel_webhook_url,
                    panel_embed
                )

                if success and new_message_id:
                    message_id = new_message_id
                    # Update message ID in settings
                    await update_settings(current_user["id"], {"discord_webhook_message_id": message_id})
                    updated_settings["discord_webhook_message_id"] = message_id
        else:
            # Send new message
            success, new_message_id, error = await send_discord_webhook(
                webhook.panel_webhook_url,
                panel_embed
            )

            if success and new_message_id:
                message_id = new_message_id
                # Update message ID in settings
                await update_settings(current_user["id"], {"discord_webhook_message_id": message_id})
                updated_settings["discord_webhook_message_id"] = message_id

    # For backward compatibility, also update bot status webhook if configured
    # This can be removed in the future when all users have migrated to the combined webhook
    if webhook.bot_webhook_url:
        # Create bot-only status embed for backward compatibility
        bot_embed = create_bot_status_embed()

        # Check if we have a message ID for the bot webhook
        bot_message_id = webhook.bot_message_id or updated_settings.get("discord_bot_webhook_message_id")

        if bot_message_id:
            # Update existing message
            success, error = await update_discord_webhook(
                webhook.bot_webhook_url,
                bot_message_id,
                bot_embed
            )

            if not success and "Unknown Message" in (error or ""):
                # Message was deleted, send a new one
                success, new_bot_message_id, error = await send_discord_webhook(
                    webhook.bot_webhook_url,
                    bot_embed
                )

                if success and new_bot_message_id:
                    # Update message ID in settings
                    await update_settings(current_user["id"], {"discord_bot_webhook_message_id": new_bot_message_id})
                    updated_settings["discord_bot_webhook_message_id"] = new_bot_message_id
        else:
            # Send new message
            success, new_bot_message_id, error = await send_discord_webhook(
                webhook.bot_webhook_url,
                bot_embed
            )

            if success and new_bot_message_id:
                # Update message ID in settings
                await update_settings(current_user["id"], {"discord_bot_webhook_message_id": new_bot_message_id})
                updated_settings["discord_bot_webhook_message_id"] = new_bot_message_id

    return DiscordWebhookResponse(
        panel_webhook_url=updated_settings.get("discord_panel_webhook_url"),
        bot_webhook_url=updated_settings.get("discord_bot_webhook_url"),
        message_id=updated_settings.get("discord_webhook_message_id"),
        bot_message_id=updated_settings.get("discord_bot_webhook_message_id")
    )

@router.post("/discord/test")
async def test_discord_webhook(current_user: dict = Depends(get_current_active_user)):
    """Test the Discord webhooks by sending current status."""
    settings = await get_settings(current_user["id"])

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord webhook not configured"
        )

    panel_result = None
    bot_result = None

    # Test panel webhook with combined panel and bot status
    if settings.get("discord_panel_webhook_url"):
        # Create combined panel and bot status embed
        panel_embed = create_panel_status_embed()

        if settings.get("discord_webhook_message_id"):
            # Update existing message
            success, error = await update_discord_webhook(
                settings["discord_panel_webhook_url"],
                settings["discord_webhook_message_id"],
                panel_embed
            )

            if success:
                panel_result = "Updated existing message with combined panel and bot status"
            else:
                if "Unknown Message" in (error or ""):
                    # Message was deleted, send a new one
                    success, message_id, error = await send_discord_webhook(
                        settings["discord_panel_webhook_url"],
                        panel_embed
                    )

                    if success and message_id:
                        # Update message ID in settings
                        await update_settings(current_user["id"], {"discord_webhook_message_id": message_id})
                        panel_result = "Sent new message with combined panel and bot status (previous was deleted)"
                    else:
                        panel_result = f"Error sending new message: {error}"
                else:
                    panel_result = f"Error updating message: {error}"
        else:
            # Send new message
            success, message_id, error = await send_discord_webhook(
                settings["discord_panel_webhook_url"],
                panel_embed
            )

            if success and message_id:
                # Update message ID in settings
                await update_settings(current_user["id"], {"discord_webhook_message_id": message_id})
                panel_result = "Sent new message with combined panel and bot status"
            else:
                panel_result = f"Error sending message: {error}"

    # Test bot webhook
    if settings.get("discord_bot_webhook_url"):
        bot_embed = create_bot_status_embed()

        if settings.get("discord_bot_webhook_message_id"):
            # Update existing message
            success, error = await update_discord_webhook(
                settings["discord_bot_webhook_url"],
                settings["discord_bot_webhook_message_id"],
                bot_embed
            )

            if success:
                bot_result = "Updated existing bot message"
            else:
                if "Unknown Message" in (error or ""):
                    # Message was deleted, send a new one
                    success, message_id, error = await send_discord_webhook(
                        settings["discord_bot_webhook_url"],
                        bot_embed
                    )

                    if success and message_id:
                        # Update message ID in settings
                        await update_settings(current_user["id"], {"discord_bot_webhook_message_id": message_id})
                        bot_result = "Sent new bot message (previous was deleted)"
                    else:
                        bot_result = f"Error sending new bot message: {error}"
                else:
                    bot_result = f"Error updating bot message: {error}"
        else:
            # Send new message
            success, message_id, error = await send_discord_webhook(
                settings["discord_bot_webhook_url"],
                bot_embed
            )

            if success and message_id:
                # Update message ID in settings
                await update_settings(current_user["id"], {"discord_bot_webhook_message_id": message_id})
                bot_result = "Sent new bot message"
            else:
                bot_result = f"Error sending bot message: {error}"

    return {
        "panel_webhook": panel_result or "Not configured",
        "bot_webhook": bot_result or "Not configured"
    }