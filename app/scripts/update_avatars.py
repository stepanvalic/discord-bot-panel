#!/usr/bin/env python3
"""
Script to update Discord avatars
This script is meant to be run periodically (e.g., via cron)
"""
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/avatar_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("avatar_update")

# Import avatar update function
from app.utils.discord_avatar import update_all_avatars

if __name__ == "__main__":
    logger.info(f"Avatar update script started at {datetime.now().isoformat()}")
    
    # Run avatar update
    try:
        result = update_all_avatars()
        if result:
            logger.info("Avatar update completed successfully")
        else:
            logger.info("Avatar update skipped or failed")
    except Exception as e:
        logger.error(f"Error during avatar update: {e}")
        
    logger.info(f"Avatar update script finished at {datetime.now().isoformat()}")
