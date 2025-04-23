import os
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/panel_status.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("panel_status")

# Global variables
START_TIME = time.time()
PROCESS = psutil.Process(os.getpid())

def get_panel_status() -> Dict[str, Any]:
    """
    Get the current status of the panel
    """
    try:
        # Calculate uptime
        uptime = time.time() - START_TIME
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Get memory usage
        memory_info = PROCESS.memory_info()
        memory_usage = f"{memory_info.rss / (1024 * 1024):.2f} MB"
        
        # Get CPU usage
        cpu_usage = f"{PROCESS.cpu_percent(interval=0.1):.2f}%"
        
        return {
            "uptime": uptime_str,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "pid": PROCESS.pid,
            "start_time": datetime.fromtimestamp(START_TIME).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting panel status: {e}")
        return {
            "uptime": "Unknown",
            "memory_usage": "Unknown",
            "cpu_usage": "Unknown",
            "error": str(e)
        }
