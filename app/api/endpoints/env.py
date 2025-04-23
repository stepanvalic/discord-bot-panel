from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import os
import re
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.schemas.env import EnvVariables, BotEntrypoint, VenvSetting

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/env.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("env")

router = APIRouter()


def parse_env_file(file_path: str) -> dict:
    """
    Parse an .env file into a dictionary
    """
    variables = {}

    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse the line
                match = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line)

                if match:
                    key = match.group(1)
                    value = match.group(2)

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                    variables[key] = value
    except FileNotFoundError:
        # File doesn't exist yet
        pass
    except Exception as e:
        logger.error(f"Error parsing .env file: {e}")

    return variables


def write_env_file(file_path: str, variables: dict) -> None:
    """
    Write a dictionary to an .env file
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            for key, value in variables.items():
                # Check if the value needs quotes
                if " " in value or "=" in value:
                    value = f'"{value}"'

                f.write(f"{key}={value}\n")
    except Exception as e:
        logger.error(f"Error writing .env file: {e}")
        raise


@router.get("", response_model=EnvVariables)
async def get_env_variables(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the environment variables
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Get the .env file path
    env_file = os.path.join("work-bot", ".env")

    # Parse the .env file
    variables = parse_env_file(env_file)

    return {"variables": variables}


@router.put("", response_model=EnvVariables)
async def update_env_variables(
    env_data: EnvVariables,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Update the environment variables
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Get the .env file path
    env_file = os.path.join("work-bot", ".env")

    try:
        # Write the .env file
        write_env_file(env_file, env_data.variables)

        return env_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating .env file: {str(e)}")


@router.get("/entrypoint", response_model=BotEntrypoint)
async def get_bot_entrypoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the bot entrypoint
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"entrypoint": settings.bot_entrypoint}


@router.put("/entrypoint", response_model=BotEntrypoint)
async def update_bot_entrypoint(
    entrypoint_data: BotEntrypoint,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Update the bot entrypoint
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update the entrypoint
    settings.bot_entrypoint = entrypoint_data.entrypoint
    db.commit()

    return entrypoint_data


@router.get("/venv", response_model=VenvSetting)
async def get_venv_setting(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the bot venv setting
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"use_venv": settings.bot_venv}


@router.put("/venv", response_model=VenvSetting)
async def update_venv_setting(
    venv_data: VenvSetting,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Update the bot venv setting
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update the venv setting
    settings.bot_venv = venv_data.use_venv
    db.commit()

    return {"use_venv": settings.bot_venv}
