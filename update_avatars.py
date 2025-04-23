#!/usr/bin/env python3
import os
import sys
import logging
from app.utils.discord_avatar import update_all_avatars

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/manual_avatar_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("manual_avatar_update")

def main():
    """
    Run avatar update manually
    """
    logger.info("Starting manual avatar update")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Force update
    result = update_all_avatars(force=True)
    
    if result:
        logger.info("Avatar update completed successfully")
    else:
        logger.error("Avatar update failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
