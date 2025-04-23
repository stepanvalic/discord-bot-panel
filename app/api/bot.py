from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import time
import json

from app.auth.auth import get_current_active_user, get_current_admin_user
from app.bot.manager import get_bot_status, start_bot, stop_bot, restart_bot, get_bot_logs, get_bot_settings, update_bot_settings, install_requirements
from app.models.models import BotStatus, BotSettings, BotSettingsUpdate

router = APIRouter()

# WebSocket connections
active_connections: List[WebSocket] = []

@router.get("/status", response_model=BotStatus)
async def bot_status(current_user: dict = Depends(get_current_active_user)):
    """Get the current status of the bot."""
    status = get_bot_status()
    return BotStatus(**status)

@router.post("/start", response_model=BotStatus)
async def bot_start(current_user: dict = Depends(get_current_active_user)):
    """Start the bot."""
    result = start_bot()
    return BotStatus(**result)

@router.post("/stop", response_model=BotStatus)
async def bot_stop(current_user: dict = Depends(get_current_active_user)):
    """Stop the bot."""
    result = stop_bot()
    return BotStatus(**result)

@router.post("/restart", response_model=BotStatus)
async def bot_restart(current_user: dict = Depends(get_current_active_user)):
    """Restart the bot."""
    result = restart_bot()
    return BotStatus(**result)

@router.get("/logs")
async def bot_logs(limit: int = 100, current_user: dict = Depends(get_current_active_user)):
    """Get the most recent bot logs."""
    logs = get_bot_logs(limit)
    return {"logs": logs}

@router.get("/settings", response_model=BotSettings)
async def get_settings(current_user: dict = Depends(get_current_active_user)):
    """Get the current bot settings."""
    settings = get_bot_settings()
    return BotSettings(**settings)

@router.put("/settings", response_model=BotSettings)
async def update_settings(settings: BotSettingsUpdate, current_user: dict = Depends(get_current_admin_user)):
    """Update the bot settings."""
    # Update bot script, bot install path, and editable files if provided
    updated_settings = update_bot_settings(
        settings.bot_script,
        settings.bot_install_path,
        settings.editable_files
    )
    return BotSettings(**updated_settings)

@router.post("/install-requirements")
async def install_bot_requirements(current_user: dict = Depends(get_current_admin_user)):
    """Install requirements from requirements.txt in the bot's virtual environment."""
    result = install_requirements()
    return result

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for streaming bot logs."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial logs
        logs = get_bot_logs(100)
        await websocket.send_json({"logs": logs})

        # Send initial status
        status = get_bot_status()
        await websocket.send_json({"status": status})

        # Send initial settings
        settings = get_bot_settings()
        await websocket.send_json({"settings": settings})

        # Keep the connection open and periodically send updates
        last_log_count = len(logs)
        last_status_update = time.time()
        update_interval = 1.0  # Update every second
        status_update_interval = 2.0  # Update status every 2 seconds

        while True:
            await asyncio.sleep(update_interval)
            current_time = time.time()

            # Get current logs
            current_logs = get_bot_logs()
            current_log_count = len(current_logs)

            # If there are new logs, send them
            if current_log_count > last_log_count:
                new_logs = current_logs[last_log_count:]
                await websocket.send_json({"logs": new_logs})
                last_log_count = current_log_count

            # Update status less frequently to reduce overhead
            if current_time - last_status_update >= status_update_interval:
                status = get_bot_status()
                await websocket.send_json({"status": status})
                last_status_update = current_time

            # Check for client messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                try:
                    message = json.loads(data)
                    # Handle client messages here if needed
                    if message.get("type") == "get_status":
                        status = get_bot_status()
                        await websocket.send_json({"status": status})
                    elif message.get("type") == "get_settings":
                        settings = get_bot_settings()
                        await websocket.send_json({"settings": settings})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)
