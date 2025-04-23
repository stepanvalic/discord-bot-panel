from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session, get_current_admin_from_session
from app.schemas.files import FileContent, FileList, WhitelistUpdate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/files.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("files")

router = APIRouter()


def is_file_whitelisted(file_path: str, whitelist: str) -> bool:
    """
    Check if a file is in the whitelist
    """
    whitelist_items = [item.strip() for item in whitelist.split(",")]

    # Check if the file is in the whitelist
    for item in whitelist_items:
        if file_path == item or file_path.startswith(f"{item}/"):
            return True

    return False


@router.get("", response_model=FileList)
async def get_whitelisted_files(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the list of whitelisted files
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Get the whitelist
    whitelist = settings.env_whitelist
    whitelist_items = [item.strip() for item in whitelist.split(",")]

    # Get the list of files
    files = []
    work_dir = "work-bot"

    for item in whitelist_items:
        item_path = os.path.join(work_dir, item)

        if os.path.isfile(item_path):
            files.append(item)
        elif os.path.isdir(item_path):
            # Add all files in the directory
            for root, _, filenames in os.walk(item_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, work_dir)
                    files.append(rel_path)

    return {"files": files}


@router.get("/whitelist", response_model=WhitelistUpdate)
async def get_whitelist(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current whitelist
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"whitelist": settings.env_whitelist}


@router.put("/whitelist", response_model=WhitelistUpdate)
async def update_whitelist(
    whitelist_data: WhitelistUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Update the whitelist (admin only)
    """
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update the whitelist
    settings.env_whitelist = whitelist_data.whitelist
    db.commit()

    return {"whitelist": settings.env_whitelist}


@router.get("/{file_path:path}", response_model=FileContent)
async def get_file_content(
    file_path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the content of a file
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Check if the file is in the whitelist
    if not is_file_whitelisted(file_path, settings.env_whitelist):
        raise HTTPException(status_code=403, detail="File not in whitelist")

    # Get the file content
    file_path = os.path.join("work-bot", file_path)

    try:
        with open(file_path, "r") as f:
            content = f.read()

        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.put("/{file_path:path}", response_model=FileContent)
async def update_file_content(
    file_path: str,
    file_data: FileContent,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Update the content of a file
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Check if the file is in the whitelist
    if not is_file_whitelisted(file_path, settings.env_whitelist):
        raise HTTPException(status_code=403, detail="File not in whitelist")

    # Update the file content
    file_path = os.path.join("work-bot", file_path)

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(file_data.content)

        return {"content": file_data.content}
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")
