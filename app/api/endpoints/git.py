from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
import subprocess
import logging
import re

from app.utils.ssh import ensure_ssh_configured

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/git.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("git")

router = APIRouter()

# Constants
WORK_DIR = "work-bot"


@router.get("/status")
async def get_git_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current Git repository status
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if the repository exists
    git_dir = os.path.join(WORK_DIR, ".git")
    if not os.path.exists(git_dir):
        raise HTTPException(status_code=404, detail="No Git repository found")

    try:
        # Get repository URL
        repo_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=WORK_DIR,
            text=True
        ).strip()

        # Get current branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=WORK_DIR,
            text=True
        ).strip()

        # Get last commit
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h - %s (%an, %ar)"],
            cwd=WORK_DIR,
            text=True
        ).strip()

        return {
            "repository": repo_url,
            "branch": branch,
            "last_commit": last_commit
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting Git status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting Git status: {e}")


@router.post("/clone")
async def clone_repository(
    repo_data: Dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Clone a Git repository
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get repository URL and branch
    repo_url = repo_data.get("url")
    branch = repo_data.get("branch")

    if not repo_url:
        raise HTTPException(status_code=400, detail="Repository URL is required")

    # Check if the repository URL is valid
    if not re.match(r'^git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\.git$', repo_url):
        raise HTTPException(status_code=400, detail="Invalid SSH repository URL format")

    try:
        # Ensure SSH is configured before cloning
        private_key_file = ensure_ssh_configured()

        # Check if the work directory already has a Git repository
        git_dir = os.path.join(WORK_DIR, ".git")
        if os.path.exists(git_dir):
            # Remove the existing repository
            subprocess.run(
                ["rm", "-rf", WORK_DIR],
                check=True
            )

            # Recreate the work directory
            os.makedirs(WORK_DIR, exist_ok=True)

        # Set environment with GIT_SSH_COMMAND to use our specific key
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = f"ssh -i {private_key_file} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

        # Clone the repository
        if branch:
            subprocess.run(
                ["git", "clone", "-b", branch, repo_url, WORK_DIR],
                check=True,
                env=env
            )
        else:
            subprocess.run(
                ["git", "clone", repo_url, WORK_DIR],
                check=True,
                env=env
            )

        logger.info(f"Repository {repo_url} cloned successfully")
        return {"status": "success", "message": f"Repository {repo_url} cloned successfully"}
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning repository: {e}")
        raise HTTPException(status_code=500, detail=f"Error cloning repository: {e}")


@router.post("/pull")
async def pull_repository(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Pull the latest changes from the Git repository
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if the repository exists
    git_dir = os.path.join(WORK_DIR, ".git")
    if not os.path.exists(git_dir):
        raise HTTPException(status_code=404, detail="No Git repository found")

    try:
        # Ensure SSH is configured before pulling
        private_key_file = ensure_ssh_configured()

        # Set environment with GIT_SSH_COMMAND to use our specific key
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = f"ssh -i {private_key_file} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

        # Pull the latest changes
        output = subprocess.check_output(
            ["git", "pull"],
            cwd=WORK_DIR,
            text=True,
            stderr=subprocess.STDOUT,
            env=env
        ).strip()

        logger.info(f"Repository pulled successfully: {output}")
        return {"status": "success", "message": output}
    except subprocess.CalledProcessError as e:
        logger.error(f"Error pulling repository: {e.output}")
        raise HTTPException(status_code=500, detail=f"Error pulling repository: {e.output}")
