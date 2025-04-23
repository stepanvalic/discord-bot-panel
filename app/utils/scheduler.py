import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Coroutine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store scheduled tasks
scheduled_tasks: Dict[str, asyncio.Task] = {}

async def run_periodic(interval_seconds: int, func: Callable[..., Coroutine], *args, **kwargs) -> None:
    """
    Run a function periodically at the specified interval.
    
    Args:
        interval_seconds: The interval in seconds between function calls
        func: The async function to call
        *args, **kwargs: Arguments to pass to the function
    """
    while True:
        try:
            await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in scheduled task {func.__name__}: {str(e)}")
        
        # Wait for the next interval
        await asyncio.sleep(interval_seconds)

def schedule_task(name: str, interval_seconds: int, func: Callable[..., Coroutine], *args, **kwargs) -> None:
    """
    Schedule a task to run periodically.
    
    Args:
        name: A unique name for the task
        interval_seconds: The interval in seconds between function calls
        func: The async function to call
        *args, **kwargs: Arguments to pass to the function
    """
    if name in scheduled_tasks and not scheduled_tasks[name].done():
        logger.warning(f"Task {name} is already scheduled. Cancelling the existing task.")
        scheduled_tasks[name].cancel()
    
    task = asyncio.create_task(run_periodic(interval_seconds, func, *args, **kwargs))
    scheduled_tasks[name] = task
    logger.info(f"Scheduled task {name} to run every {interval_seconds} seconds")

def cancel_task(name: str) -> bool:
    """
    Cancel a scheduled task.
    
    Args:
        name: The name of the task to cancel
        
    Returns:
        True if the task was cancelled, False if it wasn't found or was already done
    """
    if name in scheduled_tasks:
        task = scheduled_tasks[name]
        if not task.done():
            task.cancel()
            logger.info(f"Cancelled task {name}")
            return True
    
    logger.warning(f"Task {name} not found or already done")
    return False

def get_task_status(name: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a scheduled task.
    
    Args:
        name: The name of the task
        
    Returns:
        A dictionary with task status information, or None if the task wasn't found
    """
    if name in scheduled_tasks:
        task = scheduled_tasks[name]
        return {
            "name": name,
            "done": task.done(),
            "cancelled": task.cancelled(),
            "exception": str(task.exception()) if task.done() and not task.cancelled() and task.exception() else None
        }
    
    return None

def get_all_tasks() -> Dict[str, Dict[str, Any]]:
    """
    Get the status of all scheduled tasks.
    
    Returns:
        A dictionary mapping task names to their status information
    """
    return {
        name: {
            "name": name,
            "done": task.done(),
            "cancelled": task.cancelled(),
            "exception": str(task.exception()) if task.done() and not task.cancelled() and task.exception() else None
        }
        for name, task in scheduled_tasks.items()
    }

# Initialize scheduler
def init_scheduler():
    """Initialize the scheduler with periodic tasks."""
    from app.utils.discord_webhook import update_discord_status_webhooks
    
    # Schedule Discord webhook updates every 60 seconds
    schedule_task("discord_webhook_update", 60, update_discord_status_webhooks)
    
    logger.info("Scheduler initialized with periodic tasks")
