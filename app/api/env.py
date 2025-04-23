from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.auth.auth import get_current_active_user
from app.models.models import EnvVariables
from app.utils.file_editor import read_file_content, write_file_content

router = APIRouter()

def parse_env_file(content: str) -> Dict[str, str]:
    """Parse an .env file into a dictionary."""
    variables = {}
    
    for line in content.splitlines():
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
        
        # Split by the first equals sign
        parts = line.split("=", 1)
        if len(parts) == 2:
            key, value = parts
            variables[key.strip()] = value.strip()
    
    return variables

def format_env_file(variables: Dict[str, str]) -> str:
    """Format a dictionary into an .env file."""
    lines = []
    
    for key, value in variables.items():
        lines.append(f"{key}={value}")
    
    return "\n".join(lines)

@router.get("/", response_model=EnvVariables)
async def get_env_variables(current_user: dict = Depends(get_current_active_user)):
    """Get the environment variables from the .env file."""
    # Read the .env file
    content = read_file_content(".env")
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=".env file not found"
        )
    
    # Parse the .env file
    variables = parse_env_file(content)
    
    return EnvVariables(variables=variables)

@router.put("/", response_model=EnvVariables)
async def update_env_variables(env_variables: EnvVariables, current_user: dict = Depends(get_current_active_user)):
    """Update the environment variables in the .env file."""
    # Format the .env file
    content = format_env_file(env_variables.variables)
    
    # Write the .env file
    success = write_file_content(".env", content)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write .env file"
        )
    
    return env_variables
