from pydantic import BaseModel
from typing import Dict, Any


class EnvVariables(BaseModel):
    """
    Environment variables schema
    """
    variables: Dict[str, str]


class BotEntrypoint(BaseModel):
    """
    Bot entrypoint schema
    """
    entrypoint: str


class VenvSetting(BaseModel):
    """
    Virtual environment setting schema
    """
    use_venv: bool = True
