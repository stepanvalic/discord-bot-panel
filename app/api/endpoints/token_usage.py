from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
from typing import Dict, List, Any

from app.db.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("")
async def get_token_usage(current_user: User = Depends(get_current_user)):
    """
    Get token usage data from the token_usage.json file
    """
    try:
        # Path to the token usage file
        token_usage_path = os.path.join("work-bot", "token_usage.json")
        
        # Check if the file exists
        if not os.path.exists(token_usage_path):
            # Return empty data if file doesn't exist
            return {"entries": []}
        
        # Read the file
        with open(token_usage_path, "r") as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading token usage data: {str(e)}")
