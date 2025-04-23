from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.schemas.ssh import SSHKeyResponse
from app.utils.ssh import generate_ssh_key_pair

router = APIRouter()


@router.get("", response_model=SSHKeyResponse)
async def get_ssh_key(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current SSH public key
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the settings
    settings = db.query(Settings).first()

    if not settings or not settings.ssh_public_key:
        raise HTTPException(status_code=404, detail="SSH key not found")

    return {"public_key": settings.ssh_public_key}


@router.post("/generate", response_model=SSHKeyResponse)
async def generate_ssh_key(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Generate a new SSH key pair
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # Generate a new SSH key pair
        public_key, private_key = generate_ssh_key_pair()

        # Get the settings
        settings = db.query(Settings).first()

        if not settings:
            # Create settings if they don't exist
            settings = Settings(
                ssh_public_key=public_key,
                ssh_private_key=private_key
            )
            db.add(settings)
        else:
            # Update existing settings
            settings.ssh_public_key = public_key
            settings.ssh_private_key = private_key

        db.commit()

        return {"public_key": public_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SSH key: {str(e)}")
