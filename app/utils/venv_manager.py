import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Get logger
logger = logging.getLogger("discord-bot-panel")

# Constants
WORK_DIR = "work-bot"
VENV_DIR = os.path.join(WORK_DIR, "venv")
REQUIREMENTS_FILE = os.path.join(WORK_DIR, "requirements.txt")

# Get absolute paths
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ABS_WORK_DIR = os.path.join(BASE_DIR, WORK_DIR)
ABS_VENV_DIR = os.path.join(BASE_DIR, VENV_DIR)
ABS_REQUIREMENTS_FILE = os.path.join(BASE_DIR, REQUIREMENTS_FILE)


def create_venv() -> Tuple[bool, str]:
    """
    Create a virtual environment for the bot
    Returns a tuple of (success, message)
    """
    try:
        # Ensure the work directory exists
        os.makedirs(ABS_WORK_DIR, exist_ok=True)

        # Check if venv already exists
        if os.path.exists(ABS_VENV_DIR):
            return True, "Virtual environment already exists"

        # Create the virtual environment
        logger.info(f"Creating virtual environment in {ABS_VENV_DIR}")
        subprocess.run(
            [sys.executable, "-m", "venv", ABS_VENV_DIR],
            check=True
        )

        # Upgrade pip
        pip_path = os.path.join(ABS_VENV_DIR, "bin", "pip")
        subprocess.run(
            [pip_path, "install", "--upgrade", "pip"],
            check=True
        )

        return True, "Virtual environment created successfully"
    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        return False, f"Error creating virtual environment: {e}"


def install_requirements() -> Tuple[bool, str, List[str]]:
    """
    Install requirements from requirements.txt
    Returns a tuple of (success, message, log_lines)
    """
    log_lines = []

    try:
        # Check if venv exists
        if not os.path.exists(ABS_VENV_DIR):
            success, message = create_venv()
            if not success:
                return False, message, log_lines
            log_lines.append(message)

        # Create requirements.txt if it doesn't exist
        if not os.path.exists(ABS_REQUIREMENTS_FILE):
            logger.info(f"Creating default requirements.txt in {ABS_REQUIREMENTS_FILE}")
            with open(ABS_REQUIREMENTS_FILE, "w") as f:
                f.write("discord.py==2.3.2\npython-dotenv==1.0.0\n")
            log_lines.append("Created default requirements.txt with discord.py and python-dotenv")

        # Install requirements
        pip_path = os.path.join(ABS_VENV_DIR, "bin", "pip")
        logger.info(f"Installing requirements from {ABS_REQUIREMENTS_FILE}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Absolute requirements file path: {ABS_REQUIREMENTS_FILE}")
        logger.info(f"Absolute pip path: {pip_path}")

        # First, make sure pip is up to date
        upgrade_process = subprocess.Popen(
            [pip_path, "install", "--upgrade", "pip"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Capture output from pip upgrade
        while True:
            line = upgrade_process.stdout.readline()
            if not line and upgrade_process.poll() is not None:
                break
            if line:
                log_line = line.strip()
                log_lines.append(log_line)
                logger.info(log_line)

        # Now install the requirements
        process = subprocess.Popen(
            [pip_path, "install", "-r", ABS_REQUIREMENTS_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Capture output
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_line = line.strip()
                log_lines.append(log_line)
                logger.info(log_line)

        # Check if installation was successful
        if process.returncode == 0:
            return True, "Requirements installed successfully", log_lines
        else:
            return False, f"Error installing requirements (exit code {process.returncode})", log_lines
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False, f"Error installing requirements: {e}", log_lines


def get_python_path() -> str:
    """
    Get the path to the Python executable in the virtual environment
    """
    # Check if we're on Windows or Unix/Linux
    if os.name == "nt":  # Windows
        return os.path.join(ABS_VENV_DIR, "Scripts", "python.exe")
    else:  # Unix/Linux
        return os.path.join(ABS_VENV_DIR, "bin", "python")


def get_requirements() -> Tuple[bool, str, List[str]]:
    """
    Get the contents of requirements.txt
    Returns a tuple of (success, message, requirements)
    """
    try:
        if not os.path.exists(ABS_REQUIREMENTS_FILE):
            return True, "No requirements file found", []

        with open(ABS_REQUIREMENTS_FILE, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

        return True, "Requirements retrieved successfully", requirements
    except Exception as e:
        logger.error(f"Error getting requirements: {e}")
        return False, f"Error getting requirements: {e}", []
