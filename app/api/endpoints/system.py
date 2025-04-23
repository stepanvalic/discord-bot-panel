from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user_from_session
from app.utils.system_dependencies import check_system_dependencies, install_linux_dependencies
import platform

router = APIRouter()


@router.get("/dependencies/check")
async def check_dependencies(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Check if the system has the required dependencies
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check system dependencies
    success, message = check_system_dependencies()
    
    return {
        "success": success,
        "message": message,
        "system": platform.system(),
        "python_version": platform.python_version()
    }


@router.post("/dependencies/install")
async def install_dependencies(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Install the required system dependencies
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check the operating system
    system = platform.system()
    if system != "Linux":
        raise HTTPException(status_code=400, detail=f"Automatic installation is only supported on Linux, not {system}")
    
    # Install system dependencies
    success, message, logs = install_linux_dependencies()
    
    return {
        "success": success,
        "message": message,
        "logs": logs
    }
