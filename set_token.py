#!/usr/bin/env python3
import sqlite3
import sys

# Database path
DB_PATH = "data.db"

def set_discord_bot_token(token):
    """
    Set Discord bot token in the database
    """
    if not token:
        print("Error: Token is required")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if not cursor.fetchone():
            print("Error: Settings table does not exist")
            conn.close()
            return False
        
        # Check if there's a settings record
        cursor.execute("SELECT COUNT(*) FROM settings")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert a new settings record
            print("Creating new settings record...")
            cursor.execute(
                "INSERT INTO settings (discord_bot_token, avatar_update_interval) VALUES (?, ?)",
                (token, 60)
            )
        else:
            # Update existing settings record
            print("Updating existing settings record...")
            cursor.execute(
                "UPDATE settings SET discord_bot_token = ? WHERE id = 1",
                (token,)
            )
        
        # Commit the changes
        conn.commit()
        print(f"Discord bot token set successfully: {token[:5]}... (length: {len(token)})")
        
        # Verify the token was set
        cursor.execute("SELECT discord_bot_token FROM settings LIMIT 1")
        result = cursor.fetchone()
        if result and result[0] == token:
            print("Verification successful")
        else:
            print("Verification failed")
        
        # Close the connection
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting Discord bot token: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_token.py <discord_bot_token>")
        sys.exit(1)
    
    token = sys.argv[1]
    if set_discord_bot_token(token):
        print("Token set successfully")
    else:
        print("Failed to set token")
        sys.exit(1)
