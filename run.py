#!/usr/bin/env python3
import os
import sys
import logging
import uvicorn
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord-bot-panel")

def setup_environment():
    """
    Set up the environment for the application
    """
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("work-bot", exist_ok=True)
    
    # Check if the database exists, if not initialize it
    if not os.path.exists("data.db"):
        logger.info("Database not found, initializing...")
        try:
            from app.db.init_db import init_db
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            sys.exit(1)

def main():
    """
    Main entry point for the application
    """
    parser = argparse.ArgumentParser(description="Discord Bot Panel")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()
    
    # Set up the environment
    setup_environment()
    
    # Start the application
    logger.info(f"Starting Discord Bot Panel on {args.host}:{args.port}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
