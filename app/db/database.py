import os
import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLite database path
DB_PATH = os.path.join(os.getcwd(), "app.db")

# Initialize database
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Create users table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create settings table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            ssh_public_key TEXT,
            ssh_private_key TEXT,
            git_repo_url TEXT,
            webhook_url TEXT,
            webhook_key TEXT,
            discord_panel_webhook_url TEXT,
            discord_bot_webhook_url TEXT,
            discord_webhook_message_id TEXT,
            discord_bot_webhook_message_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()

# Initialize database
# We'll initialize the database when the application starts
# This will be handled by a startup event in main.py

# Helper function to convert SQLite row to dict
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Database operations using SQLite
async def get_user(username: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            async with db.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
                user = await cursor.fetchone()
                return user
    except Exception as e:
        print(f"Error in get_user: {e}")
        return None

async def create_user(username: str, password_hash: str, role: str = "user"):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            cursor = await db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            await db.commit()
            user_id = cursor.lastrowid

            # Get the created user
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()
                return user
    except Exception as e:
        print(f"Error in create_user: {e}")
        return None

async def get_users():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            async with db.execute("SELECT * FROM users") as cursor:
                users = await cursor.fetchall()
                return users
    except Exception as e:
        print(f"Error in get_users: {e}")
        return []

async def update_user(user_id: int, data: dict):
    try:
        # Build SET clause and parameters
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        params = list(data.values()) + [user_id]

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", params)
            await db.commit()

            # Get the updated user
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()
                return user
    except Exception as e:
        print(f"Error in update_user: {e}")
        return None

async def delete_user(user_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            # Get the user before deleting
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()

            # Delete the user
            await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await db.commit()

            return user
    except Exception as e:
        print(f"Error in delete_user: {e}")
        return None

# Database operations for settings
async def get_settings(user_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            async with db.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,)) as cursor:
                settings = await cursor.fetchone()
                return settings
    except Exception as e:
        print(f"Error in get_settings: {e}")
        return None

async def create_settings(user_id: int, ssh_public_key: str = None, ssh_private_key: str = None,
                         git_repo_url: str = None, webhook_url: str = None, webhook_key: str = None,
                         discord_panel_webhook_url: str = None, discord_bot_webhook_url: str = None,
                         discord_webhook_message_id: str = None, discord_bot_webhook_message_id: str = None):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            cursor = await db.execute(
                "INSERT INTO settings (user_id, ssh_public_key, ssh_private_key, git_repo_url, webhook_url, webhook_key, discord_panel_webhook_url, discord_bot_webhook_url, discord_webhook_message_id, discord_bot_webhook_message_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, ssh_public_key or '', ssh_private_key or '', git_repo_url or '', webhook_url or '', webhook_key or '', discord_panel_webhook_url or '', discord_bot_webhook_url or '', discord_webhook_message_id or '', discord_bot_webhook_message_id or '')
            )
            await db.commit()
            settings_id = cursor.lastrowid

            # Get the created settings
            async with db.execute("SELECT * FROM settings WHERE id = ?", (settings_id,)) as cursor:
                settings = await cursor.fetchone()
                return settings
    except Exception as e:
        print(f"Error in create_settings: {e}")
        return None

async def update_settings(user_id: int, data: dict):
    try:
        # Build SET clause and parameters
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        params = list(data.values()) + [user_id]

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = dict_factory
            await db.execute(f"UPDATE settings SET {set_clause} WHERE user_id = ?", params)
            await db.commit()

            # Get the updated settings
            async with db.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,)) as cursor:
                settings = await cursor.fetchone()
                return settings
    except Exception as e:
        print(f"Error in update_settings: {e}")
        return None

# Check if database is initialized
async def is_db_initialized():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] > 0
    except Exception as e:
        print(f"Error in is_db_initialized: {e}")
        return False
