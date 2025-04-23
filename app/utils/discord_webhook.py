import os
import json
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Import bot manager functions
from app.bot.manager import get_bot_status

async def send_discord_webhook(webhook_url: str, content: Dict[Any, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Send a message to a Discord webhook.

    Args:
        webhook_url: The Discord webhook URL
        content: The content to send (embed data)

    Returns:
        Tuple of (success, message_id, error_message)
    """
    if not webhook_url:
        return False, None, "No webhook URL provided"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=content) as response:
                if response.status == 204 or response.status == 200:
                    # Get message ID from response headers or body
                    response_data = None
                    try:
                        response_data = await response.json()
                    except:
                        pass

                    message_id = None
                    if response_data and 'id' in response_data:
                        message_id = response_data['id']

                    return True, message_id, None
                else:
                    error_text = await response.text()
                    return False, None, f"Error {response.status}: {error_text}"
    except Exception as e:
        return False, None, f"Exception: {str(e)}"

async def update_discord_webhook(webhook_url: str, message_id: str, content: Dict[Any, Any]) -> Tuple[bool, Optional[str]]:
    """
    Update an existing message sent via a Discord webhook.

    Args:
        webhook_url: The Discord webhook URL
        message_id: The ID of the message to update
        content: The new content (embed data)

    Returns:
        Tuple of (success, error_message)
    """
    if not webhook_url or not message_id:
        return False, "No webhook URL or message ID provided"

    # Discord webhook API for editing messages
    edit_url = f"{webhook_url}/messages/{message_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(edit_url, json=content) as response:
                if response.status == 204 or response.status == 200:
                    return True, None
                else:
                    error_text = await response.text()
                    return False, f"Error {response.status}: {error_text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def create_panel_status_embed() -> Dict[str, Any]:
    """Create an embed with the panel and bot status information."""
    now = datetime.now()

    # Get system information
    import platform
    import psutil

    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    # Get bot status
    bot_status = get_bot_status()

    # Determine bot status emoji and color
    bot_status_emoji = "❓"
    if bot_status["status"] == "running":
        bot_status_emoji = "✅"
    elif bot_status["status"] == "stopped":
        bot_status_emoji = "⛔"
    elif bot_status["status"] == "error":
        bot_status_emoji = "⚠️"

    # Create bot status value
    bot_status_value = f"{bot_status_emoji} {bot_status['status'].capitalize()}"

    # Add uptime if available
    if bot_status.get("uptime"):
        bot_status_value += f"\nUptime: {bot_status['uptime']}"

    # Add PID if available
    if bot_status.get("pid"):
        bot_status_value += f"\nPID: {bot_status['pid']}"

    # Add memory and CPU usage if available
    if bot_status.get("memory_usage"):
        bot_status_value += f"\nMemory: {bot_status['memory_usage']}"

    if bot_status.get("cpu_usage"):
        bot_status_value += f"\nCPU: {bot_status['cpu_usage']}"

    # Create embed
    embed = {
        "embeds": [
            {
                "title": "Discord Bot Panel Status",
                "description": "Current status of the Discord Bot Panel and Bot",
                "color": 3447003,  # Blue color
                "fields": [
                    {
                        "name": "Panel System",
                        "value": f"OS: {platform.system()} {platform.release()}\nPython: {platform.python_version()}",
                        "inline": True
                    },
                    {
                        "name": "Panel Resources",
                        "value": f"CPU: {cpu_percent}%\nMemory: {memory_percent}%\nDisk: {disk_percent}%",
                        "inline": True
                    },
                    {
                        "name": "Panel Status",
                        "value": "✅ Online",
                        "inline": True
                    },
                    {
                        "name": "Bot Status",
                        "value": bot_status_value,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
    }

    # Add error if available
    if bot_status.get("error"):
        embed["embeds"][0]["fields"].append({
            "name": "Bot Error",
            "value": f"```{bot_status['error']}```",
            "inline": False
        })

    return embed

def create_bot_status_embed() -> Dict[str, Any]:
    """Create an embed with the bot status information."""
    now = datetime.now()

    # Get bot status
    bot_status = get_bot_status()

    # Determine status emoji
    status_emoji = "❓"
    status_color = 10197915  # Gray color

    if bot_status["status"] == "running":
        status_emoji = "✅"
        status_color = 5763719  # Green color
    elif bot_status["status"] == "stopped":
        status_emoji = "⛔"
        status_color = 15548997  # Red color
    elif bot_status["status"] == "error":
        status_emoji = "⚠️"
        status_color = 16776960  # Yellow color

    # Create embed
    embed = {
        "embeds": [
            {
                "title": "Discord Bot Status",
                "description": "Current status of the Discord Bot",
                "color": status_color,
                "fields": [
                    {
                        "name": "Status",
                        "value": f"{status_emoji} {bot_status['status'].capitalize()}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
    }

    # Add uptime if available
    if bot_status.get("uptime"):
        embed["embeds"][0]["fields"].append({
            "name": "Uptime",
            "value": bot_status["uptime"],
            "inline": True
        })

    # Add PID if available
    if bot_status.get("pid"):
        embed["embeds"][0]["fields"].append({
            "name": "Process ID",
            "value": str(bot_status["pid"]),
            "inline": True
        })

    # Add error if available
    if bot_status.get("error"):
        embed["embeds"][0]["fields"].append({
            "name": "Error",
            "value": f"```{bot_status['error']}```",
            "inline": False
        })

    return embed

async def update_discord_status_webhooks():
    """Update all Discord status webhooks."""
    try:
        from app.db.database import get_users, get_settings, update_settings

        # Get all users
        users = await get_users()

        for user in users:
            try:
                # Get user settings
                settings = await get_settings(user["id"])

                if not settings:
                    continue

                # Create combined panel and bot status embed
                panel_embed = create_panel_status_embed()

                # Update panel status webhook
                if settings.get("discord_panel_webhook_url"):
                    if settings.get("discord_webhook_message_id"):
                        # Update existing message
                        success, error = await update_discord_webhook(
                            settings["discord_panel_webhook_url"],
                            settings["discord_webhook_message_id"],
                            panel_embed
                        )

                        if not success and "Unknown Message" in (error or ""):
                            # Message was deleted, send a new one
                            success, message_id, error = await send_discord_webhook(
                                settings["discord_panel_webhook_url"],
                                panel_embed
                            )

                            if success and message_id:
                                # Update message ID in settings
                                await update_settings(user["id"], {"discord_webhook_message_id": message_id})
                    else:
                        # Send new message
                        success, message_id, error = await send_discord_webhook(
                            settings["discord_panel_webhook_url"],
                            panel_embed
                        )

                        if success and message_id:
                            # Update message ID in settings
                            await update_settings(user["id"], {"discord_webhook_message_id": message_id})

                # For backward compatibility, also update bot status webhook if configured
                # This can be removed in the future when all users have migrated to the combined webhook
                if settings.get("discord_bot_webhook_url"):
                    # Create bot-only status embed for backward compatibility
                    bot_embed = create_bot_status_embed()

                    if settings.get("discord_bot_webhook_message_id"):
                        # Update existing message
                        success, error = await update_discord_webhook(
                            settings["discord_bot_webhook_url"],
                            settings["discord_bot_webhook_message_id"],
                            bot_embed
                        )

                        if not success and "Unknown Message" in (error or ""):
                            # Message was deleted, send a new one
                            success, message_id, error = await send_discord_webhook(
                                settings["discord_bot_webhook_url"],
                                bot_embed
                            )

                            if success and message_id:
                                # Update message ID in settings
                                await update_settings(user["id"], {"discord_bot_webhook_message_id": message_id})
                    else:
                        # Send new message
                        success, message_id, error = await send_discord_webhook(
                            settings["discord_bot_webhook_url"],
                            bot_embed
                        )

                        if success and message_id:
                            # Update message ID in settings
                            await update_settings(user["id"], {"discord_bot_webhook_message_id": message_id})
            except Exception as e:
                import logging
                logging.error(f"Error updating Discord webhook for user {user['id']}: {str(e)}")
    except Exception as e:
        import logging
        logging.error(f"Error in update_discord_status_webhooks: {str(e)}")
