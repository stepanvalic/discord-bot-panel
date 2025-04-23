from pydantic import BaseModel
from typing import Optional


class BotStatus(BaseModel):
    """
    Bot status schema
    """
    running: bool
    pid: Optional[int] = None
    uptime: Optional[str] = None
    entrypoint: str


class BotLogs(BaseModel):
    """
    Bot logs schema
    """
    logs: list[str]
