import os
import sqlite3

# SQLite database path
DB_PATH = os.path.join(os.getcwd(), "app.db")

def migrate_database():
    """Add new columns to settings table if they don't exist."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the columns exist
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add the git_repo_url column if it doesn't exist
        if "git_repo_url" not in columns:
            print("Adding git_repo_url column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN git_repo_url TEXT")
            conn.commit()
            print("Column git_repo_url added successfully.")
        else:
            print("Column git_repo_url already exists.")

        # Add the discord_panel_webhook_url column if it doesn't exist
        if "discord_panel_webhook_url" not in columns:
            print("Adding discord_panel_webhook_url column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN discord_panel_webhook_url TEXT")
            conn.commit()
            print("Column discord_panel_webhook_url added successfully.")
        else:
            print("Column discord_panel_webhook_url already exists.")

        # Add the discord_bot_webhook_url column if it doesn't exist
        if "discord_bot_webhook_url" not in columns:
            print("Adding discord_bot_webhook_url column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN discord_bot_webhook_url TEXT")
            conn.commit()
            print("Column discord_bot_webhook_url added successfully.")
        else:
            print("Column discord_bot_webhook_url already exists.")

        # Add the discord_webhook_message_id column if it doesn't exist
        if "discord_webhook_message_id" not in columns:
            print("Adding discord_webhook_message_id column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN discord_webhook_message_id TEXT")
            conn.commit()
            print("Column discord_webhook_message_id added successfully.")
        else:
            print("Column discord_webhook_message_id already exists.")

        # Add the discord_bot_webhook_message_id column if it doesn't exist
        if "discord_bot_webhook_message_id" not in columns:
            print("Adding discord_bot_webhook_message_id column to settings table...")
            cursor.execute("ALTER TABLE settings ADD COLUMN discord_bot_webhook_message_id TEXT")
            conn.commit()
            print("Column discord_bot_webhook_message_id added successfully.")
        else:
            print("Column discord_bot_webhook_message_id already exists.")

        # Close the connection
        conn.close()

        return True
    except Exception as e:
        print(f"Error migrating database: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
