from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.bot.manager import install_bot_requirements, get_install_logs, get_bot_requirements

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/requirements.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("requirements")

router = APIRouter()


@router.get("")
async def get_requirements(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the bot requirements
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get the requirements
    success, message, requirements = get_bot_requirements()
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
    
    return {
        "requirements": requirements,
        "message": message
    }


@router.post("/install")
async def install_requirements(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Install the bot requirements
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Install requirements in the background
    background_tasks.add_task(install_requirements_task)
    
    return {"status": "Installation started"}


@router.get("/logs")
async def get_logs(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the installation logs
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get the logs
    logs = get_install_logs()
    
    return {"logs": logs}


async def install_requirements_task():
    """
    Background task to install requirements
    """
    try:
        install_bot_requirements()
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
