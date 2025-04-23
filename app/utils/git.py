import os
import subprocess
import shutil
from pathlib import Path

def get_bot_directory():
    """Get the bot directory from config or use default."""
    # Get from environment variables if available
    from dotenv import load_dotenv
    load_dotenv()

    bot_dir = os.getenv("BOT_DIR", "./workspace")

    # If it's a relative path, make it absolute
    if not os.path.isabs(bot_dir):
        bot_dir = os.path.join(os.getcwd(), bot_dir.lstrip("./"))

    return bot_dir

def ensure_bot_directory():
    """Ensure the bot directory exists."""
    bot_dir = get_bot_directory()
    os.makedirs(bot_dir, exist_ok=True)
    return bot_dir

def is_git_repo():
    """Check if the bot directory is a git repository."""
    bot_dir = get_bot_directory()
    git_dir = os.path.join(bot_dir, ".git")
    return os.path.exists(git_dir)

def clone_repository(repo_url):
    """Clone a git repository to the bot directory."""
    bot_dir = get_bot_directory()

    # If the directory exists and is not empty, remove it
    if os.path.exists(bot_dir) and os.listdir(bot_dir):
        shutil.rmtree(bot_dir)
        os.makedirs(bot_dir, exist_ok=True)

    # Clone the repository
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, bot_dir],
            check=True,
            capture_output=True,
            text=True
        )
        return {"success": True, "message": "Repository cloned successfully."}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to clone repository: {e.stderr}"}

def pull_repository():
    """Pull the latest changes from the remote repository."""
    bot_dir = get_bot_directory()

    # Check if the directory is a git repository
    if not is_git_repo():
        return {"success": False, "message": "Not a git repository. Please clone the repository first."}

    # Pull the latest changes
    try:
        result = subprocess.run(
            ["git", "pull"],
            check=True,
            capture_output=True,
            text=True,
            cwd=bot_dir
        )
        return {"success": True, "message": "Repository updated successfully.", "details": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to pull repository: {e.stderr}"}
