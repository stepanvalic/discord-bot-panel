from fastapi import APIRouter

from app.api.endpoints import bot, ssh, webhook, files, env, status, requirements, git, system, discord_settings, ip_bans, token_usage

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(bot.router, prefix="/bot", tags=["bot"])
api_router.include_router(ssh.router, prefix="/ssh-keys", tags=["ssh"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(env.router, prefix="/env", tags=["env"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["requirements"])
api_router.include_router(git.router, prefix="/git", tags=["git"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(discord_settings.router, prefix="/discord", tags=["discord"])
api_router.include_router(ip_bans.router, prefix="/ip-bans", tags=["ip-bans"])
api_router.include_router(token_usage.router, prefix="/token-usage", tags=["token-usage"])
