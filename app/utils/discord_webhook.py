import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/discord_webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_webhook")

class DiscordWebhook:
    """
    Discord webhook utility for sending status updates
    """
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.message_id = None

    def send_status_update(
        self,
        bot_status: Dict[str, Any],
        panel_status: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send a status update to Discord with both bot and panel status
        Returns the message ID if successful
        """
        if not self.webhook_url:
            logger.warning("No webhook URL configured")
            return None

        # Create embeds for bot and panel status
        embeds = [
            self._create_bot_embed(bot_status),
            self._create_panel_embed(panel_status)
        ]

        # Prepare payload
        payload = {
            "embeds": embeds,
            "username": "Bot Control Panel",
            "avatar_url": "https://raw.githubusercontent.com/stepanvalic/discord-bot-panel/77121cb0fa4a994c144eb5e8d8f93275145c4c9c/app/static/img/webhook-panel-image.png"  # Use the webhook panel image
        }

        try:
            # If we have a message ID, try to edit the existing message
            if message_id:
                try:
                    response = requests.patch(
                        f"{self.webhook_url}/messages/{message_id}",
                        json=payload
                    )

                    # If the message doesn't exist anymore, send a new one
                    if response.status_code == 404:
                        logger.warning(f"Message {message_id} not found, sending new message")
                        response = requests.post(
                            self.webhook_url,
                            json=payload
                        )
                except Exception as e:
                    logger.warning(f"Failed to update message, sending new one: {e}")
                    response = requests.post(
                        self.webhook_url,
                        json=payload
                    )
            else:
                # Otherwise, send a new message
                response = requests.post(
                    self.webhook_url,
                    json=payload
                )

            if response.status_code in (200, 204):
                # If this was a new message, get the message ID
                if response.status_code == 200:
                    try:
                        data = response.json()
                        message_id = data.get("id")
                        self.message_id = message_id
                    except Exception as e:
                        logger.warning(f"Failed to parse response JSON: {e}")

                logger.info(f"Status update sent successfully (Message ID: {message_id})")
                return message_id
            else:
                logger.error(f"Failed to send status update: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return None

    def _create_bot_embed(self, bot_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an embed for bot status
        """
        is_running = bot_status.get("running", False)
        status_text = "Online" if is_running else "Offline"
        status_color = 0x00FF00 if is_running else 0xFF0000  # Green if online, red if offline

        fields = [
            {
                "name": "Status",
                "value": status_text,
                "inline": True
            }
        ]

        # Add PID if bot is running
        if is_running and bot_status.get("pid"):
            fields.append({
                "name": "PID",
                "value": str(bot_status.get("pid")),
                "inline": True
            })

        # Add uptime if bot is running
        if is_running and bot_status.get("uptime"):
            fields.append({
                "name": "Uptime",
                "value": bot_status.get("uptime"),
                "inline": True
            })

        # Add entrypoint
        if bot_status.get("entrypoint"):
            fields.append({
                "name": "Entrypoint",
                "value": f"`{bot_status.get('entrypoint')}`",
                "inline": True
            })

        return {
            "title": "Bot Status",
            "color": status_color,
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_panel_embed(self, panel_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an embed for panel status
        """
        uptime = panel_status.get("uptime", "Unknown")
        memory_usage = panel_status.get("memory_usage", "Unknown")
        cpu_usage = panel_status.get("cpu_usage", "Unknown")

        fields = [
            {
                "name": "Uptime",
                "value": uptime,
                "inline": True
            },
            {
                "name": "Memory Usage",
                "value": memory_usage,
                "inline": True
            },
            {
                "name": "CPU Usage",
                "value": cpu_usage,
                "inline": True
            }
        ]

        return {
            "title": "Panel Status",
            "color": 0x3498DB,  # Blue
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
