#!/usr/bin/env python3
import sqlite3
import os

# Database path
DB_PATH = "data.db"

def check_database():
    """
    Check the database for Discord bot token and users with Discord ID
    """
    print(f"Checking database at {os.path.abspath(DB_PATH)}")
    
    # Check if the database file exists
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} does not exist")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check settings table
        print("\nChecking settings table...")
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Settings table columns: {columns}")
        
        if "discord_bot_token" in columns:
            cursor.execute("SELECT discord_bot_token FROM settings LIMIT 1")
            result = cursor.fetchone()
            if result and result[0]:
                token = result[0]
                print(f"Discord bot token found: {token[:5]}... (length: {len(token)})")
            else:
                print("No Discord bot token found in settings table")
        else:
            print("discord_bot_token column does not exist in settings table")
        
        # Check users table
        print("\nChecking users table...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Users table columns: {columns}")
        
        if "discord_id" in columns:
            cursor.execute("SELECT id, username, discord_id FROM users WHERE discord_id IS NOT NULL AND discord_id != ''")
            users = cursor.fetchall()
            print(f"Found {len(users)} users with Discord ID:")
            for user in users:
                print(f"  User ID: {user[0]}, Username: {user[1]}, Discord ID: {user[2]}")
        else:
            print("discord_id column does not exist in users table")
        
        # Check if discord_avatar_url column exists
        if "discord_avatar_url" in columns:
            cursor.execute("SELECT id, username, discord_avatar_url FROM users WHERE discord_avatar_url IS NOT NULL")
            users = cursor.fetchall()
            print(f"\nFound {len(users)} users with Discord avatar URL:")
            for user in users:
                print(f"  User ID: {user[0]}, Username: {user[1]}, Avatar URL: {user[2]}")
        else:
            print("\ndiscord_avatar_url column does not exist in users table")
        
        # Close the connection
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
