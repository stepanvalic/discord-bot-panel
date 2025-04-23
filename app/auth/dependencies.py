from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.utils.security import SECRET_KEY, ALGORITHM

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# In-memory session store (would be replaced with Redis or similar in production)
SESSION_STORE: Dict[str, Dict[str, Any]] = {}


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user
    """
    if token is None:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            return None
    except JWTError:
        return None

    # Get the user from the database
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        return None

    return user


async def get_current_user_from_session(
    request: Request,
    session: str = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from session cookie
    """
    if not session or session not in SESSION_STORE:
        return None

    user_id = SESSION_STORE[session].get("user_id")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


async def get_current_admin_from_session(
    current_user: Optional[User] = Depends(get_current_user_from_session)
) -> Optional[User]:
    """
    Get the current authenticated admin user from session
    """
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user


async def get_current_admin(current_user: Optional[User] = Depends(get_current_user)) -> Optional[User]:
    """
    Get the current authenticated admin user
    """
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user
