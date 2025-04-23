import sqlite3
import os
import logging

# Get logger
logger = logging.getLogger("discord-bot-panel")

# Database path
DB_PATH = "data.db"

def run_migrations():
    """
    Run database migrations
    """
    logger.info("Running database migrations...")

    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database file {DB_PATH} not found")
        return

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the list of columns in the settings table
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add webhook_message_id column if it doesn't exist
        if "webhook_message_id" not in columns:
            logger.info("Adding webhook_message_id column to settings table")
            cursor.execute("ALTER TABLE settings ADD COLUMN webhook_message_id TEXT")

        # Add bot_venv column if it doesn't exist
        if "bot_venv" not in columns:
            logger.info("Adding bot_venv column to settings table")
            cursor.execute("ALTER TABLE settings ADD COLUMN bot_venv BOOLEAN DEFAULT 1")

        # Add discord_bot_token column if it doesn't exist
        if "discord_bot_token" not in columns:
            logger.info("Adding discord_bot_token column to settings table")
            cursor.execute("ALTER TABLE settings ADD COLUMN discord_bot_token TEXT")

        # Add avatar_update_interval column if it doesn't exist
        if "avatar_update_interval" not in columns:
            logger.info("Adding avatar_update_interval column to settings table")
            cursor.execute("ALTER TABLE settings ADD COLUMN avatar_update_interval INTEGER DEFAULT 60")

        # Add last_avatar_update column if it doesn't exist
        if "last_avatar_update" not in columns:
            logger.info("Adding last_avatar_update column to settings table")
            cursor.execute("ALTER TABLE settings ADD COLUMN last_avatar_update TIMESTAMP")

        # Get the list of columns in the users table
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]

        # Add discord_id column if it doesn't exist
        if "discord_id" not in user_columns:
            logger.info("Adding discord_id column to users table")
            # SQLite doesn't support adding a UNIQUE constraint to an existing table directly
            # So we add the column without the constraint
            cursor.execute("ALTER TABLE users ADD COLUMN discord_id TEXT")

        # Add avatar_url column if it doesn't exist
        if "avatar_url" not in user_columns:
            logger.info("Adding avatar_url column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")

        # Add discord_avatar_url column if it doesn't exist
        if "discord_avatar_url" not in user_columns:
            logger.info("Adding discord_avatar_url column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN discord_avatar_url TEXT")

        # Add last_avatar_update column if it doesn't exist
        if "last_avatar_update" not in user_columns:
            logger.info("Adding last_avatar_update column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN last_avatar_update TIMESTAMP")

        # Commit the changes
        conn.commit()
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()
