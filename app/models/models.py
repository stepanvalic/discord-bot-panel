from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class User(BaseModel):
    id: Optional[int] = None
    username: str
    password_hash: str
    role: str = "user"
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class Settings(BaseModel):
    id: Optional[int] = None
    user_id: int
    ssh_public_key: Optional[str] = None
    ssh_private_key: Optional[str] = None
    git_repo_url: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_key: Optional[str] = None
    discord_panel_webhook_url: Optional[str] = None
    discord_bot_webhook_url: Optional[str] = None
    discord_webhook_message_id: Optional[str] = None
    created_at: Optional[datetime] = None

class SettingsResponse(BaseModel):
    id: int
    ssh_public_key: Optional[str] = None
    git_repo_url: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_key: Optional[str] = None
    discord_panel_webhook_url: Optional[str] = None
    discord_bot_webhook_url: Optional[str] = None
    discord_webhook_message_id: Optional[str] = None
    created_at: datetime

class SSHSettings(BaseModel):
    git_repo_url: str

class BotStatus(BaseModel):
    status: str  # "running", "stopped", "error"
    pid: Optional[int] = None
    uptime: Optional[str] = None
    memory_usage: Optional[str] = None
    cpu_usage: Optional[str] = None
    bot_dir: Optional[str] = None
    bot_script: Optional[str] = None
    log_count: Optional[int] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None

class WebhookCreate(BaseModel):
    url: str

class WebhookResponse(BaseModel):
    url: str
    key: str

class DiscordWebhookCreate(BaseModel):
    panel_webhook_url: Optional[str] = None
    panel_message_id: Optional[str] = None
    bot_webhook_url: Optional[str] = None
    bot_message_id: Optional[str] = None

class DiscordWebhookResponse(BaseModel):
    panel_webhook_url: Optional[str] = None
    bot_webhook_url: Optional[str] = None
    message_id: Optional[str] = None
    bot_message_id: Optional[str] = None

class FileContent(BaseModel):
    content: str

class FileResponse(BaseModel):
    path: str
    content: str

class FilesList(BaseModel):
    files: List[str]

class EnvVariables(BaseModel):
    variables: dict[str, str]

class BotSettings(BaseModel):
    bot_dir: str
    bot_script: str
    bot_venv: str
    bot_install_path: Optional[str] = None
    editable_files: List[str] = Field(default_factory=list)

class BotSettingsUpdate(BaseModel):
    bot_script: str
    bot_install_path: Optional[str] = None
    editable_files: Optional[List[str]] = None
