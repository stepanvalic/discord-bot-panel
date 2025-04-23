import os
import glob
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bot directory from environment variables
bot_dir_env = os.getenv("BOT_DIR", "./workspace")
# Make sure we have an absolute path
BOT_DIR = os.path.abspath(bot_dir_env) if os.path.isabs(bot_dir_env) else os.path.abspath(os.path.join(os.getcwd(), bot_dir_env.lstrip("./")))

# Import editable files manager
from app.utils.editable_files import is_file_editable

def is_file_whitelisted(file_path: str) -> bool:
    """Check if a file is whitelisted for editing."""
    # Use the is_file_editable function from the editable_files module
    return is_file_editable(file_path)

def get_all_files() -> List[dict]:
    """Get a list of all files in the bot directory with their editable status."""
    # Use the global BOT_DIR variable
    global BOT_DIR

    # Reload environment variables to get the latest bot directory
    load_dotenv()
    bot_dir_env = os.getenv("BOT_DIR", "./workspace")
    # Update the global BOT_DIR variable
    BOT_DIR = os.path.abspath(bot_dir_env) if os.path.isabs(bot_dir_env) else os.path.abspath(os.path.join(os.getcwd(), bot_dir_env.lstrip("./")))

    # Ensure bot directory exists
    os.makedirs(BOT_DIR, exist_ok=True)

    # Get all files in the bot directory
    all_files = []
    for root, dirs, files in os.walk(BOT_DIR):
        # Skip hidden directories (starting with .)
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            # Skip hidden files (starting with .)
            if file.startswith('.'):
                continue

            # Get the relative path from the bot directory
            rel_path = os.path.relpath(os.path.join(root, file), BOT_DIR)

            # Check if the file is editable
            editable = is_file_whitelisted(file)

            all_files.append({
                "path": rel_path,
                "editable": editable
            })

    # Sort files by path
    all_files.sort(key=lambda x: x["path"])

    return all_files

def get_whitelisted_files() -> List[str]:
    """Get a list of all files in the bot directory (for backward compatibility)."""
    files = get_all_files()
    return [file["path"] for file in files]

def read_file_content(file_path: str) -> Optional[str]:
    """Read the content of a file."""
    # Use the global BOT_DIR variable
    global BOT_DIR

    # Reload environment variables to get the latest bot directory
    load_dotenv()
    bot_dir_env = os.getenv("BOT_DIR", "./workspace")
    # Update the global BOT_DIR variable
    BOT_DIR = os.path.abspath(bot_dir_env) if os.path.isabs(bot_dir_env) else os.path.abspath(os.path.join(os.getcwd(), bot_dir_env.lstrip("./")))

    # Get the absolute path
    abs_path = os.path.join(BOT_DIR, file_path)

    # Check if the file exists
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        return None

    # Read the file content
    try:
        with open(abs_path, "r") as f:
            return f.read()
    except Exception:
        return None

def write_file_content(file_path: str, content: str) -> bool:
    """Write content to a file."""
    # Check if the file is whitelisted
    if not is_file_whitelisted(file_path):
        return False

    # Use the global BOT_DIR variable
    global BOT_DIR

    # Reload environment variables to get the latest bot directory
    load_dotenv()
    bot_dir_env = os.getenv("BOT_DIR", "./workspace")
    # Update the global BOT_DIR variable
    BOT_DIR = os.path.abspath(bot_dir_env) if os.path.isabs(bot_dir_env) else os.path.abspath(os.path.join(os.getcwd(), bot_dir_env.lstrip("./")))

    # Get the absolute path
    abs_path = os.path.join(BOT_DIR, file_path)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    # Write the file content
    try:
        with open(abs_path, "w") as f:
            f.write(content)
        return True
    except Exception:
        return False
