from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Cookie, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio

from app.db.session import get_db
from app.models.user import User
from app.models.settings import Settings
from app.auth.dependencies import get_current_user_from_session
from app.schemas.bot import BotStatus, BotLogs
from app.bot.manager import get_bot_status, start_bot, stop_bot, restart_bot, get_bot_logs, read_bot_log_file

router = APIRouter()


@router.get("/status", response_model=BotStatus)
async def bot_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the current status of the bot
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the bot entrypoint from settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Get the bot status
    status = get_bot_status(settings.bot_entrypoint)

    return status


@router.post("/start", response_model=BotStatus)
async def start_bot_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Start the bot
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the bot entrypoint from settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    try:
        # Start the bot
        result = start_bot(settings.bot_entrypoint, settings.bot_venv)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Handle form submission (redirect back to dashboard)
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            return RedirectResponse(url="/", status_code=303)

        return result
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger("discord-bot-panel")
        logger.error(f"Error starting bot: {str(e)}")

        # Return error
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


@router.post("/stop", response_model=BotStatus)
async def stop_bot_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Stop the bot
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get the bot entrypoint from settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    try:
        # Stop the bot
        result = stop_bot(settings.bot_entrypoint)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Handle form submission (redirect back to dashboard)
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            return RedirectResponse(url="/", status_code=303)

        return result
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger("discord-bot-panel")
        logger.error(f"Error stopping bot: {str(e)}")

        # Return error
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


@router.post("/restart", response_model=BotStatus)
async def restart_bot_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Restart the bot
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Get the bot entrypoint from settings
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    try:
        # Restart the bot
        result = restart_bot(settings.bot_entrypoint, settings.bot_venv)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Handle form submission (redirect back to dashboard)
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            return RedirectResponse(url="/", status_code=303)

        return result
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger("discord-bot-panel")
        logger.error(f"Error restarting bot: {str(e)}")

        # Return error
        raise HTTPException(status_code=500, detail=f"Failed to restart bot: {str(e)}")


@router.get("/logs", response_model=BotLogs)
async def bot_logs(
    request: Request,
    limit: int = 100,
    current_user: Optional[User] = Depends(get_current_user_from_session)
):
    """
    Get the bot logs
    """
    # Check if user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    logs = get_bot_logs(limit)
    return {"logs": logs}


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for live bot logs
    """
    await websocket.accept()

    try:
        # Get all available logs
        current_logs = get_bot_logs(1000)  # Get all available logs

        # If no logs are available, send a waiting message
        if not current_logs or current_logs[0] == "No logs available":
            await websocket.send_text("Connected to bot logs. Waiting for output...")
            # Try to get logs from file
            file_logs = read_bot_log_file(1000)
            if file_logs and file_logs[0] != "No logs available":
                for log in file_logs:
                    await websocket.send_text(log)
        else:
            # Send all available logs
            for log in current_logs:
                await websocket.send_text(log)

        # Track which logs we've already sent
        last_log_count = len(current_logs) if current_logs and current_logs[0] != "No logs available" else 0

        # Keep the connection open and send new logs
        while True:
            # Get current logs
            current_logs = get_bot_logs(1000)  # Get all available logs

            # Check if we have new logs
            if len(current_logs) > last_log_count:
                # Send only the new logs
                new_logs = current_logs[last_log_count:]
                for log in new_logs:
                    await websocket.send_text(log)

                # Update the count
                last_log_count = len(current_logs)

            # Wait a short time before checking for new logs
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Log any errors
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(f"Error: {e}")
        except:
            pass
