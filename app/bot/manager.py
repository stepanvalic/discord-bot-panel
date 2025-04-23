import os
import subprocess
import signal
import time
import psutil
from typing import Optional, Dict, Any, Tuple, List
import logging
from pathlib import Path

from app.utils.venv_manager import get_python_path, create_venv, install_requirements, get_requirements

# Get logger
logger = logging.getLogger("discord-bot-panel")

# Global variables
BOT_PROCESS = None
BOT_START_TIME = None
WORK_DIR = "work-bot"
INSTALL_LOGS = []
BOT_LOGS = []  # Store bot logs in memory

# Get absolute paths
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ABS_WORK_DIR = os.path.join(BASE_DIR, WORK_DIR)
ABS_LOG_DIR = os.path.join(BASE_DIR, "logs")


def get_bot_status(entrypoint: str) -> Dict[str, Any]:
    """
    Get the current status of the bot
    """
    global BOT_PROCESS, BOT_START_TIME

    # Check if the process is running
    if BOT_PROCESS is not None:
        try:
            # Check if the process is still running
            if BOT_PROCESS.poll() is None:
                # Calculate uptime
                uptime = time.time() - BOT_START_TIME
                hours, remainder = divmod(uptime, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

                return {
                    "running": True,
                    "pid": BOT_PROCESS.pid,
                    "uptime": uptime_str,
                    "entrypoint": entrypoint
                }
        except Exception as e:
            logger.error(f"Error checking bot status: {e}")

    # Check if there's a bot process running even if BOT_PROCESS is None
    try:
        # Use psutil to find Python processes that might be our bot
        bot_path = os.path.join(ABS_WORK_DIR, entrypoint)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if this is a Python process
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    # Check if the command line contains our bot path
                    if proc.info['cmdline'] and any(bot_path in cmd for cmd in proc.info['cmdline']):
                        pid = proc.info['pid']
                        process = psutil.Process(pid)
                        create_time = process.create_time()
                        BOT_START_TIME = create_time
                        # Calculate uptime
                        uptime = time.time() - create_time
                        hours, remainder = divmod(uptime, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

                        return {
                            "running": True,
                            "pid": pid,
                            "uptime": uptime_str,
                            "entrypoint": entrypoint
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process might have terminated or we don't have access
                continue
            except Exception as e:
                logger.error(f"Error checking process: {e}")
                continue
    except Exception as e:
        logger.error(f"Error checking for bot processes: {e}")

    # Bot is not running
    return {
        "running": False,
        "pid": None,
        "uptime": None,
        "entrypoint": entrypoint
    }


def start_bot(entrypoint: str, use_venv: bool = True) -> Dict[str, Any]:
    """
    Start the bot process
    """
    global BOT_PROCESS, BOT_START_TIME

    # Check if the bot is already running
    if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
        logger.warning("Bot is already running")
        return get_bot_status(entrypoint)

    try:
        # Ensure the work directory exists
        os.makedirs(ABS_WORK_DIR, exist_ok=True)

        # Start the bot process
        bot_path = os.path.join(ABS_WORK_DIR, entrypoint)
        abs_bot_path = os.path.abspath(bot_path)

        # Check if the bot file exists
        if not os.path.exists(bot_path):
            logger.error(f"Bot file not found: {bot_path}")
            return {
                "running": False,
                "pid": None,
                "uptime": None,
                "entrypoint": entrypoint,
                "error": f"Bot file not found: {entrypoint}"
            }

        # Determine which Python executable to use
        if use_venv:
            # Check if the bot has its own virtual environment
            bot_venv_path = os.path.join(ABS_WORK_DIR, "venv", "bin", "python")
            if os.path.exists(bot_venv_path):
                python_exe = bot_venv_path
                logger.info(f"Using bot's virtual environment: {bot_venv_path}")
            else:
                # Fall back to the panel's virtual environment
                python_exe = get_python_path()
                logger.info(f"Using panel's virtual environment: {python_exe}")
        else:
            python_exe = "python"  # Use system Python
            logger.info("Using system Python")

        # Create log file
        log_file = os.path.join(ABS_LOG_DIR, "bot.log")
        os.makedirs(ABS_LOG_DIR, exist_ok=True)

        # Open log file for appending (not overwriting)
        log_fd = open(log_file, "a")

        # Start the bot process with environment variables
        env = os.environ.copy()

        # Add PYTHONPATH to include the work directory
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{WORK_DIR}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = WORK_DIR

        # Add Discord token if available
        env_file = os.path.join(ABS_WORK_DIR, '.env')
        if os.path.exists(env_file):
            logger.info("Found .env file, loading environment variables")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env[key] = value
                            logger.info(f"Loaded environment variable: {key}")
            except Exception as e:
                logger.error(f"Error loading .env file: {e}")

        # Print debug info
        logger.info(f"Starting bot with Python: {python_exe}")
        logger.info(f"Bot path: {bot_path}")
        logger.info(f"Working directory: {WORK_DIR}")

        # Start the bot process with additional error handling
        try:
            BOT_PROCESS = subprocess.Popen(
                [python_exe, abs_bot_path],
                cwd=ABS_WORK_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                # Ensure process doesn't inherit file descriptors
                close_fds=True
            )

            # Check if process started successfully
            if BOT_PROCESS.poll() is not None:
                # Process failed to start
                error_msg = f"Bot process failed to start (exit code: {BOT_PROCESS.returncode})"
                logger.error(error_msg)
                return {
                    "running": False,
                    "pid": None,
                    "uptime": None,
                    "entrypoint": entrypoint,
                    "error": error_msg
                }
        except Exception as e:
            error_msg = f"Failed to start bot process: {str(e)}"
            logger.error(error_msg)
            return {
                "running": False,
                "pid": None,
                "uptime": None,
                "entrypoint": entrypoint,
                "error": error_msg
            }

        # Start a thread to read output and write to log file
        import threading

        def log_output():
            global BOT_LOGS
            while BOT_PROCESS and BOT_PROCESS.poll() is None:
                try:
                    line = BOT_PROCESS.stdout.readline()
                    if line:
                        # Add to in-memory logs
                        BOT_LOGS.append(line.strip())
                        # Keep only the last 5000 lines
                        if len(BOT_LOGS) > 5000:
                            BOT_LOGS = BOT_LOGS[-5000:]
                        # Write to log file
                        log_fd.write(line)
                        log_fd.flush()
                except Exception as e:
                    logger.error(f"Error reading bot output: {e}")
                    break
            # Close log file when process ends
            log_fd.close()

        # Start log thread
        log_thread = threading.Thread(target=log_output, daemon=True)
        log_thread.start()

        BOT_START_TIME = time.time()
        logger.info(f"Bot started with PID {BOT_PROCESS.pid} using {'venv' if use_venv else 'system Python'}")

        return get_bot_status(entrypoint)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return {
            "running": False,
            "pid": None,
            "uptime": None,
            "entrypoint": entrypoint,
            "error": str(e)
        }


def stop_bot(entrypoint: str = "bot.py") -> Dict[str, Any]:
    """
    Stop the bot process
    """
    global BOT_PROCESS, BOT_START_TIME

    # Check if the bot is running
    if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
        logger.warning("Bot is not running")
        return {"running": False, "pid": None, "uptime": None, "entrypoint": entrypoint}

    try:
        # Get the process
        process = psutil.Process(BOT_PROCESS.pid)
        pid = process.pid
        logger.info(f"Stopping bot process with PID {pid}")

        # First try to gracefully terminate with SIGINT (CTRL+C)
        try:
            # Send CTRL+C signal to the process and its children
            for child in process.children(recursive=True):
                try:
                    logger.info(f"Sending SIGINT to child process {child.pid}")
                    child.send_signal(signal.SIGINT)  # CTRL+C signal
                except Exception as e:
                    logger.warning(f"Failed to send SIGINT to child process: {e}")

            logger.info(f"Sending SIGINT to main process {process.pid}")
            process.send_signal(signal.SIGINT)  # CTRL+C signal

            # Wait a short time for the process to handle the signal
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Error sending SIGINT: {e}")

        # If the process is still running, try SIGTERM
        try:
            if process.is_running():
                logger.info("Process still running, sending SIGTERM")
                for child in process.children(recursive=True):
                    try:
                        logger.info(f"Sending SIGTERM to child process {child.pid}")
                        child.terminate()
                    except Exception as e:
                        logger.warning(f"Failed to terminate child process: {e}")

                logger.info(f"Sending SIGTERM to main process {process.pid}")
                process.terminate()

                # Wait for the process to terminate
                try:
                    logger.info("Waiting for process to terminate...")
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    logger.warning("Process did not terminate within timeout")
                    # Force kill if it doesn't terminate
                    logger.info("Sending SIGKILL to process")
                    process.kill()
        except Exception as e:
            logger.warning(f"Error terminating process: {e}")

        # Make sure the process is actually terminated
        try:
            if process.is_running():
                logger.warning("Process still running after kill attempts, forcing kill")
                os.kill(pid, signal.SIGKILL)
        except Exception as e:
            logger.warning(f"Final kill attempt failed: {e}")

        logger.info(f"Bot stopped (PID {BOT_PROCESS.pid})")

        # Reset the process
        BOT_PROCESS = None
        BOT_START_TIME = None

        return {"running": False, "pid": None, "uptime": None, "entrypoint": entrypoint}
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return {"running": False, "pid": None, "uptime": None, "entrypoint": entrypoint, "error": str(e)}


def restart_bot(entrypoint: str, use_venv: bool = True) -> Dict[str, Any]:
    """
    Restart the bot process
    """
    stop_bot(entrypoint)
    return start_bot(entrypoint, use_venv)


def install_bot_requirements() -> Tuple[bool, str, List[str]]:
    """
    Install the bot requirements
    Returns a tuple of (success, message, log_lines)
    """
    global INSTALL_LOGS

    # Clear previous logs
    INSTALL_LOGS = []

    # Create virtual environment if it doesn't exist
    success, message = create_venv()
    INSTALL_LOGS.append(message)

    if not success:
        return False, message, INSTALL_LOGS

    # Install requirements
    success, message, logs = install_requirements()
    INSTALL_LOGS.extend(logs)

    return success, message, INSTALL_LOGS


def get_install_logs() -> List[str]:
    """
    Get the installation logs
    """
    global INSTALL_LOGS
    return INSTALL_LOGS


def get_bot_requirements() -> Tuple[bool, str, List[str]]:
    """
    Get the bot requirements
    Returns a tuple of (success, message, requirements)
    """
    return get_requirements()


def get_bot_logs(limit: int = 100) -> list[str]:
    """
    Get the bot logs
    """
    global BOT_LOGS

    try:
        # Return the last 'limit' logs from memory
        return BOT_LOGS[-limit:] if BOT_LOGS else ["No logs available"]
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        return [f"Error getting logs: {e}"]


def read_bot_log_file(limit: int = 100) -> list[str]:
    """
    Read logs from the bot log file
    """
    logs = []
    log_file = os.path.join(ABS_LOG_DIR, "bot.log")

    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                # Read the last 'limit' lines
                lines = f.readlines()
                logs = [line.strip() for line in lines[-limit:]]
    except Exception as e:
        logger.error(f"Error reading bot log file: {e}")
        logs.append(f"Error reading log file: {e}")

    return logs
