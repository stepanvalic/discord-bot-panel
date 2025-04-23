from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.ip_ban import IPBan
from app.auth.dependencies import get_current_user_from_session, get_current_admin_from_session
from app.schemas.ip_ban import IPBanResponse, IPBanUpdate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ip_bans.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ip_bans")

router = APIRouter()


@router.get("", response_model=List[IPBanResponse])
async def get_ip_bans(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Get all IP bans (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated or not admin")

    ip_bans = db.query(IPBan).all()
    return ip_bans


@router.get("/{ip_ban_id}", response_model=IPBanResponse)
async def get_ip_ban(
    ip_ban_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Get IP ban by ID (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated or not admin")

    ip_ban = db.query(IPBan).filter(IPBan.id == ip_ban_id).first()
    if not ip_ban:
        raise HTTPException(status_code=404, detail="IP ban not found")

    return ip_ban


@router.put("/{ip_ban_id}", response_model=IPBanResponse)
async def update_ip_ban(
    ip_ban_id: int,
    ip_ban_data: IPBanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_admin_from_session)
):
    """
    Update IP ban (admin only)
    """
    # Check if user is authenticated and is admin
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated or not admin")

    ip_ban = db.query(IPBan).filter(IPBan.id == ip_ban_id).first()
    if not ip_ban:
        raise HTTPException(status_code=404, detail="IP ban not found")

    # Update IP ban
    if ip_ban_data.failed_attempts is not None:
        ip_ban.failed_attempts = ip_ban_data.failed_attempts

    if ip_ban_data.is_banned is not None:
        ip_ban.is_banned = ip_ban_data.is_banned
        if ip_ban_data.is_banned is False:
            logger.info(f"IP address unbanned by admin: {ip_ban.ip_address}")

    if ip_ban_data.banned_at is not None:
        ip_ban.banned_at = ip_ban_data.banned_at

    db.commit()
    db.refresh(ip_ban)

    return ip_ban
