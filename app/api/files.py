import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from dotenv import load_dotenv

from app.auth.auth import get_current_active_user
from app.models.models import FileContent, FileResponse, FilesList
from app.utils.file_editor import get_whitelisted_files, read_file_content, write_file_content, is_file_whitelisted, get_all_files

router = APIRouter()

@router.get("/", response_model=FilesList)
async def list_files(current_user: dict = Depends(get_current_active_user)):
    """List all whitelisted files (for backward compatibility)."""
    files = get_whitelisted_files()
    return FilesList(files=files)

@router.get("/all")
async def list_all_files(current_user: dict = Depends(get_current_active_user)):
    """List all files in the bot directory with their editable status."""
    files = get_all_files()
    return {"files": files}

@router.get("/{file_path:path}", response_model=FileResponse)
async def get_file(file_path: str, current_user: dict = Depends(get_current_active_user)):
    """Get the content of a file."""
    # Reload environment variables to get the latest bot directory
    load_dotenv()
    bot_dir = os.getenv("BOT_DIR", "./workspace")

    # Get the absolute path
    abs_path = os.path.join(bot_dir, file_path)

    # Check if the file exists
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Read the file content
    try:
        with open(abs_path, "r") as f:
            content = f.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file"
        )

    return FileResponse(path=file_path, content=content)

@router.put("/{file_path:path}", response_model=FileResponse)
async def update_file(file_path: str, file_content: FileContent, current_user: dict = Depends(get_current_active_user)):
    """Update the content of a file."""
    # Check if the file is whitelisted
    if not is_file_whitelisted(file_path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File not whitelisted for editing"
        )

    # Write the file content
    success = write_file_content(file_path, file_content.content)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write file"
        )

    return FileResponse(path=file_path, content=file_content.content)
