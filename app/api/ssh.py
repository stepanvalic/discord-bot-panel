from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.auth.auth import get_current_active_user
from app.db.database import get_settings, update_settings
from app.utils.ssh import generate_ssh_key_pair, generate_ssh_key_pair_paramiko
from app.utils.git import clone_repository, pull_repository, is_git_repo
from app.models.models import SSHSettings

router = APIRouter()

@router.get("/")
async def get_ssh_key(current_user: dict = Depends(get_current_active_user)):
    """Get the current SSH public key and Git repo URL."""
    settings = await get_settings(current_user["id"])

    if not settings:
        return {"ssh_public_key": None, "git_repo_url": None}

    return {
        "ssh_public_key": settings.get("ssh_public_key"),
        "git_repo_url": settings.get("git_repo_url")
    }

@router.post("/generate")
async def generate_ssh_keys(current_user: dict = Depends(get_current_active_user)):
    """Generate a new SSH key pair."""
    try:
        # Try to generate keys using ssh-keygen
        try:
            private_key, public_key = generate_ssh_key_pair()
        except Exception:
            # Fall back to paramiko if ssh-keygen fails
            private_key, public_key = generate_ssh_key_pair_paramiko()

        # Update settings in the database
        settings = await get_settings(current_user["id"])

        if settings:
            # Update existing settings
            updated_settings = await update_settings(
                current_user["id"],
                {"ssh_private_key": private_key, "ssh_public_key": public_key}
            )
        else:
            # Create new settings
            from app.db.database import create_settings
            updated_settings = await create_settings(
                current_user["id"],
                ssh_public_key=public_key,
                ssh_private_key=private_key
            )

        if not updated_settings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save SSH keys"
            )

        return {"ssh_public_key": public_key}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SSH keys: {str(e)}"
        )

@router.post("/repo")
async def save_repo_url(repo_settings: SSHSettings, current_user: dict = Depends(get_current_active_user)):
    """Save the Git repository URL."""
    try:
        # Update settings in the database
        settings = await get_settings(current_user["id"])

        if settings:
            # Update existing settings
            updated_settings = await update_settings(
                current_user["id"],
                {"git_repo_url": repo_settings.git_repo_url}
            )
        else:
            # Create new settings
            from app.db.database import create_settings
            updated_settings = await create_settings(
                current_user["id"],
                git_repo_url=repo_settings.git_repo_url
            )

        if not updated_settings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save repository URL"
            )

        return {"git_repo_url": repo_settings.git_repo_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save repository URL: {str(e)}"
        )

@router.post("/clone")
async def clone_repo(current_user: dict = Depends(get_current_active_user)):
    """Clone the Git repository."""
    try:
        # Get the repository URL from settings
        settings = await get_settings(current_user["id"])

        if not settings or not settings.get("git_repo_url"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No repository URL set. Please set a repository URL first."
            )

        # Clone the repository
        result = clone_repository(settings["git_repo_url"])

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

        return {"message": result["message"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone repository: {str(e)}"
        )

@router.post("/pull")
async def pull_repo(current_user: dict = Depends(get_current_active_user)):
    """Pull the latest changes from the Git repository."""
    try:
        # Check if the repository is cloned
        if not is_git_repo():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please clone the repository first."
            )

        # Pull the latest changes
        result = pull_repository()

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

        return {"message": result["message"], "details": result.get("details", "")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull repository: {str(e)}"
        )

@router.get("/status")
async def repo_status(current_user: dict = Depends(get_current_active_user)):
    """Get the status of the Git repository."""
    try:
        # Check if the repository is cloned
        is_cloned = is_git_repo()

        # Get the repository URL from settings
        settings = await get_settings(current_user["id"])
        repo_url = settings.get("git_repo_url") if settings else None

        return {
            "is_cloned": is_cloned,
            "repo_url": repo_url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository status: {str(e)}"
        )
