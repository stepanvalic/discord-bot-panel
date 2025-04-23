from pydantic import BaseModel
from typing import List


class FileContent(BaseModel):
    """
    File content schema
    """
    content: str


class FileList(BaseModel):
    """
    File list schema
    """
    files: List[str]


class WhitelistUpdate(BaseModel):
    """
    Whitelist update schema
    """
    whitelist: str
