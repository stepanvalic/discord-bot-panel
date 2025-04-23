import os
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)

# Configure logger
logger = logging.getLogger("discord_avatar")
logger.setLevel(logging.INFO)

# Create a file handler for the avatar logs
file_handler = logging.FileHandler("logs/avatar_update.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# Database path
DB_PATH = "data.db"

def get_discord_bot_token() -> Optional[str]:
    """
    Get Discord bot token from settings or environment variables
    """
    # First try to get from environment variables
    logger.info("Checking for Discord bot token in environment variables...")
    env_token = os.getenv("DISCORD_BOT_TOKEN")
    if env_token:
        logger.info(f"Found Discord bot token in environment variables: {env_token[:5]}... (length: {len(env_token)})")
        return env_token
    logger.info("No Discord bot token found in environment variables")

    # If not in environment, try to get from database
    try:
        logger.info(f"Connecting to database at {DB_PATH} to get Discord bot token")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the discord_bot_token column exists
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Settings table columns: {columns}")

        if "discord_bot_token" not in columns:
            logger.error("discord_bot_token column does not exist in settings table")
            return None

        logger.info("Executing query: SELECT discord_bot_token FROM settings LIMIT 1")
        cursor.execute("SELECT discord_bot_token FROM settings LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            token = result[0]
            logger.info(f"Found Discord bot token in database: {token[:5]}... (length: {len(token)})")
            return token
        logger.info("No Discord bot token found in database")
        return None
    except Exception as e:
        logger.error(f"Error getting Discord bot token: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_avatar_update_interval() -> int:
    """
    Get avatar update interval from settings or environment variables (in minutes)
    """
    # First try to get from environment variables
    env_interval = os.getenv("AVATAR_UPDATE_INTERVAL")
    if env_interval:
        try:
            return int(env_interval)
        except ValueError:
            logger.warning(f"Invalid AVATAR_UPDATE_INTERVAL value: {env_interval}, using default")
            return 60  # Default: 60 minutes

    # If not in environment, try to get from database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT avatar_update_interval FROM settings LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return int(result[0])
        return 60  # Default: 60 minutes
    except Exception as e:
        logger.error(f"Error getting avatar update interval: {e}")
        return 60  # Default: 60 minutes

def should_update_avatars() -> bool:
    """
    Check if avatars should be updated based on the last update time and interval
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT last_avatar_update FROM settings LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        # If no last update time, should update
        if not result or not result[0]:
            return True

        # Parse last update time
        last_update = datetime.fromisoformat(result[0].replace('Z', '+00:00'))

        # Get update interval
        interval_minutes = get_avatar_update_interval()

        # Check if enough time has passed
        now = datetime.now()
        next_update = last_update + timedelta(minutes=interval_minutes)

        return now >= next_update
    except Exception as e:
        logger.error(f"Error checking if avatars should be updated: {e}")
        return True  # Default to updating if there's an error

def get_users_with_discord_id() -> List[Dict[str, Any]]:
    """
    Get all users with Discord ID
    """
    users = []
    try:
        logger.info(f"Connecting to database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if the discord_id column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"User table columns: {columns}")

        if "discord_id" not in columns:
            logger.error("discord_id column does not exist in users table")
            return []

        query = "SELECT id, username, discord_id FROM users WHERE discord_id IS NOT NULL AND discord_id != ''"
        logger.info(f"Executing query: {query}")
        cursor.execute(query)

        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} users with Discord ID")

        for row in rows:
            user = {
                "id": row["id"],
                "username": row["username"],
                "discord_id": row["discord_id"]
            }
            users.append(user)
            logger.info(f"Added user: {user}")

        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting users with Discord ID: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def update_user_avatar(user_id: int, avatar_url: str) -> bool:
    """
    Update user's Discord avatar URL
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET discord_avatar_url = ?, last_avatar_update = ? WHERE id = ?",
            (avatar_url, datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating user avatar: {e}")
        return False

def update_last_avatar_check() -> bool:
    """
    Update the last avatar check timestamp
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE settings SET last_avatar_update = ?",
            (datetime.now().isoformat(),)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating last avatar check: {e}")
        return False

def get_discord_avatar(discord_id: str, bot_token: str) -> Optional[str]:
    """
    Get Discord avatar URL for a user
    """
    try:
        # Log the attempt
        logger.info(f"Attempting to get avatar for Discord ID: {discord_id}")

        # Check if token is valid
        if not bot_token or len(bot_token) < 50:  # Discord tokens are typically longer than 50 chars
            logger.error(f"Invalid Discord bot token: {bot_token[:5]}... (length: {len(bot_token) if bot_token else 0})")
            return None

        # Discord API endpoint for user
        url = f"https://discord.com/api/v10/users/{discord_id}"
        logger.info(f"Making request to Discord API: {url}")

        # Set up headers with bot token
        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }

        # Make request to Discord API
        logger.info("Sending request to Discord API...")
        response = requests.get(url, headers=headers)
        logger.info(f"Received response with status code: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Received data from Discord API: {data}")

            # Check if user has an avatar
            if data.get("avatar"):
                # Construct avatar URL
                avatar_id = data["avatar"]
                avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_id}.png"
                logger.info(f"Generated avatar URL: {avatar_url}")
                return avatar_url
            else:
                # Use default avatar based on discriminator
                discriminator = int(discord_id) % 5
                default_url = f"https://cdn.discordapp.com/embed/avatars/{discriminator}.png"
                logger.info(f"User has no avatar, using default: {default_url}")
                return default_url
        else:
            logger.error(f"Error getting Discord avatar: {response.status_code} - {response.text}")
            # Try to parse error response
            try:
                error_data = response.json()
                logger.error(f"Error details: {error_data}")
            except:
                logger.error("Could not parse error response")
            return None
    except Exception as e:
        logger.error(f"Error getting Discord avatar: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def update_all_avatars(force: bool = False) -> bool:
    """
    Update all user avatars from Discord

    Args:
        force: If True, update avatars regardless of the last update time
    """
    # Check if we should update avatars (unless forced)
    if not force and not should_update_avatars():
        logger.info("Skipping avatar update - not time yet")
        return False

    # Get Discord bot token
    logger.info("Getting Discord bot token...")
    bot_token = get_discord_bot_token()
    if not bot_token:
        logger.error("No Discord bot token configured")
        return False
    logger.info(f"Got Discord bot token: {bot_token[:5]}... (length: {len(bot_token)})")

    # Get users with Discord ID
    logger.info("Getting users with Discord ID...")
    users = get_users_with_discord_id()
    if not users:
        logger.info("No users with Discord ID found")
        update_last_avatar_check()
        return True
    logger.info(f"Found {len(users)} users with Discord ID")
    for user in users:
        logger.info(f"User: {user['username']}, Discord ID: {user['discord_id']}")

    # Update avatars for each user
    success_count = 0
    for user in users:
        avatar_url = get_discord_avatar(user["discord_id"], bot_token)
        if avatar_url:
            if update_user_avatar(user["id"], avatar_url):
                success_count += 1
                logger.info(f"Updated avatar for user {user['username']} (ID: {user['id']})")
            else:
                logger.error(f"Failed to update avatar for user {user['username']} (ID: {user['id']})")
        else:
            logger.error(f"Failed to get Discord avatar for user {user['username']} (ID: {user['id']})")

    # Update last avatar check timestamp
    update_last_avatar_check()

    logger.info(f"Avatar update completed. Updated {success_count}/{len(users)} avatars.")
    return True

if __name__ == "__main__":
    # Run avatar update
    logger.info("Starting Discord avatar update")
    update_all_avatars()
    logger.info("Discord avatar update completed")
