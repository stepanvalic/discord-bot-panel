from pydantic import BaseModel, HttpUrl
from typing import Optional


class WebhookInfo(BaseModel):
    """
    Webhook info schema
    """
    url: Optional[str] = None
    key: str
    message_id: Optional[str] = None


class WebhookUpdate(BaseModel):
    """
    Webhook update schema
    """
    url: str
    message_id: Optional[str] = None
