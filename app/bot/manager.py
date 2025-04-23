import os
import sys
import signal
import subprocess
import time
import psutil
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bot settings from environment variables
bot_dir_env = os.getenv("BOT_DIR", os.path.join(os.getcwd(), "workspace"))
# Make sure we have an absolute path
BOT_DIR = os.path.abspath(bot_dir_env) if os.path.isabs(bot_dir_env) else os.path.abspath(os.path.join(os.getcwd(), bot_dir_env.lstrip("./")))
BOT_SCRIPT = os.getenv("BOT_SCRIPT", "bot.py")
BOT_VENV = os.getenv("BOT_VENV", "venv")
BOT_INSTALL_PATH = os.getenv("BOT_INSTALL_PATH", "")

# Import editable files manager
from app.utils.editable_files import get_editable_files, update_editable_files

# Function to update .env file with new bot script
def _update_env_file(bot_script):
    """Update the .env file with the new bot script."""
    env_path = ".env"

    # Read the current .env file
    with open(env_path, "r") as f:
        lines = f.readlines()

    # Update the BOT_SCRIPT line
    updated_lines = []
    for line in lines:
        if line.startswith("BOT_SCRIPT="):
            updated_lines.append(f"BOT_SCRIPT={bot_script}\n")
        else:
            updated_lines.append(line)

    # Write the updated .env file
    with open(env_path, "w") as f:
        f.writelines(updated_lines)

    # Update the global variable
    global BOT_SCRIPT
    BOT_SCRIPT = bot_script

# Bot process
bot_process: Optional[subprocess.Popen] = None
bot_start_time: Optional[datetime] = None
bot_logs: List[str] = []
MAX_LOGS = 1000  # Maximum number of log lines to keep in memory

def get_bot_status():
    """Get the current status of the bot."""
    global bot_process, bot_start_time

    # Get bot settings
    settings = get_bot_settings()

    if bot_process is None:
        return {
            "status": "stopped",
            "pid": None,
            "uptime": None,
            "memory_usage": None,
            "cpu_usage": None,
            "bot_dir": settings["bot_dir"],
            "bot_script": settings["bot_script"]
        }

    # Check if process is still running
    try:
        if bot_process.poll() is None:
            # Process is running
            uptime = str(datetime.now() - bot_start_time).split('.')[0] if bot_start_time else None

            # Get process resource usage
            try:
                process = psutil.Process(bot_process.pid)
                memory_usage = f"{process.memory_info().rss / (1024 * 1024):.2f} MB"
                cpu_usage = f"{process.cpu_percent(interval=0.1):.1f}%"
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                memory_usage = "N/A"
                cpu_usage = "N/A"

            return {
                "status": "running",
                "pid": bot_process.pid,
                "uptime": uptime,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "bot_dir": settings["bot_dir"],
                "bot_script": settings["bot_script"],
                "log_count": len(bot_logs)
            }
        else:
            # Process has exited
            exit_code = bot_process.returncode if bot_process else None
            bot_process = None
            bot_start_time = None
            return {
                "status": "stopped",
                "pid": None,
                "uptime": None,
                "memory_usage": None,
                "cpu_usage": None,
                "exit_code": exit_code,
                "bot_dir": settings["bot_dir"],
                "bot_script": settings["bot_script"],
                "log_count": len(bot_logs)
            }
    except Exception as e:
        # Error checking process status
        bot_process = None
        bot_start_time = None
        return {
            "status": "error",
            "pid": None,
            "uptime": None,
            "memory_usage": None,
            "cpu_usage": None,
            "error": str(e),
            "bot_dir": settings["bot_dir"],
            "bot_script": settings["bot_script"],
            "log_count": len(bot_logs)
        }

def start_bot():
    """Start the bot process."""
    global bot_process, bot_start_time, bot_logs

    # Check if bot is already running
    if bot_process is not None and bot_process.poll() is None:
        return {
            "status": "already_running",
            "pid": bot_process.pid,
            "uptime": str(datetime.now() - bot_start_time).split('.')[0] if bot_start_time else None
        }

    try:
        # Get absolute paths
        abs_bot_dir = os.path.abspath(BOT_DIR)

        # Ensure bot directory exists
        os.makedirs(abs_bot_dir, exist_ok=True)

        # Determine the correct python path based on OS
        if os.name != "nt":  # Unix/Linux/Mac
            python_path = "bin/python"
        else:  # Windows
            python_path = "Scripts\\python.exe"

        venv_path = os.path.join(abs_bot_dir, BOT_VENV)
        venv_python = os.path.join(venv_path, python_path)
        bot_script_path = os.path.join(abs_bot_dir, BOT_SCRIPT)

        # Check if the bot script exists
        if not os.path.exists(bot_script_path):
            return {
                "status": "error",
                "error": f"Bot script not found: {bot_script_path}"
            }

        # Check if the virtual environment exists, create if not
        if not os.path.exists(venv_path):
            try:
                bot_logs.append(f"Creating virtual environment at {venv_path}")
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                bot_logs.append("Virtual environment created successfully")
            except subprocess.CalledProcessError as e:
                return {
                    "status": "error",
                    "error": f"Failed to create virtual environment: {e.stderr}"
                }

        # Check if python exists in the virtual environment
        if not os.path.exists(venv_python):
            # Try to find python in the virtual environment
            if os.name != "nt":  # Unix/Linux/Mac
                possible_python_paths = [
                    os.path.join(venv_path, "bin", "python"),
                    os.path.join(venv_path, "bin", "python3")
                ]
            else:  # Windows
                possible_python_paths = [
                    os.path.join(venv_path, "Scripts", "python.exe"),
                    os.path.join(venv_path, "Scripts", "python3.exe")
                ]

            for path in possible_python_paths:
                if os.path.exists(path):
                    venv_python = path
                    break
            else:
                return {
                    "status": "error",
                    "error": f"Python interpreter not found in the virtual environment. Please check your Python installation."
                }

        # Check if requirements.txt exists and install if needed
        requirements_path = os.path.join(abs_bot_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            # Check if pip is installed in the virtual environment
            if os.name != "nt":  # Unix/Linux/Mac
                pip_path = os.path.join(venv_path, "bin", "pip")
            else:  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")

            if os.path.exists(pip_path):
                # Install requirements if they exist
                bot_logs.append(f"Installing requirements from {requirements_path}")
                try:
                    # Ensure pip is up to date
                    subprocess.run(
                        [pip_path, "install", "--upgrade", "pip"],
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=abs_bot_dir
                    )

                    # Install requirements
                    result = subprocess.run(
                        [pip_path, "install", "-r", requirements_path],
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=abs_bot_dir
                    )
                    bot_logs.append("Requirements installed successfully")

                    # Verify that python-dotenv is installed
                    try:
                        dotenv_check = subprocess.run(
                            [venv_python, "-c", "import dotenv; print('python-dotenv is installed')"],
                            check=True,
                            capture_output=True,
                            text=True,
                            cwd=abs_bot_dir
                        )
                        bot_logs.append(dotenv_check.stdout.strip())
                    except subprocess.CalledProcessError:
                        # If python-dotenv is not installed, install it directly
                        bot_logs.append("Installing python-dotenv directly...")
                        subprocess.run(
                            [pip_path, "install", "python-dotenv"],
                            check=True,
                            capture_output=True,
                            text=True,
                            cwd=abs_bot_dir
                        )
                        bot_logs.append("python-dotenv installed successfully")
                except subprocess.CalledProcessError as e:
                    bot_logs.append(f"Warning: Failed to install requirements: {e.stderr}")

        # Start the bot process
        bot_logs.append(f"Starting bot with {venv_python} {bot_script_path}")
        bot_process = subprocess.Popen(
            [venv_python, bot_script_path],
            cwd=abs_bot_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Record start time
        bot_start_time = datetime.now()

        # Start log reader thread
        import threading
        threading.Thread(target=_read_bot_logs, daemon=True).start()

        return {
            "status": "started",
            "pid": bot_process.pid,
            "uptime": "0:00:00"
        }
    except Exception as e:
        # Error starting process
        bot_process = None
        bot_start_time = None
        return {
            "status": "error",
            "error": str(e)
        }

def stop_bot():
    """Stop the bot process."""
    global bot_process, bot_start_time

    if bot_process is None or bot_process.poll() is not None:
        return {
            "status": "not_running"
        }

    try:
        # Try to terminate the process gracefully
        bot_process.terminate()

        # Wait for the process to terminate
        for _ in range(10):  # Wait up to 5 seconds
            if bot_process.poll() is not None:
                break
            time.sleep(0.5)

        # If the process is still running, kill it
        if bot_process.poll() is None:
            bot_process.kill()
            time.sleep(1)

        # Get exit code
        exit_code = bot_process.poll()

        # Reset process and start time
        bot_process = None
        bot_start_time = None

        return {
            "status": "stopped",
            "exit_code": exit_code
        }
    except Exception as e:
        # Error stopping process
        return {
            "status": "error",
            "error": str(e)
        }

def restart_bot():
    """Restart the bot process."""
    stop_result = stop_bot()
    if stop_result.get("status") in ["stopped", "not_running"]:
        return start_bot()
    else:
        return stop_result

def _read_bot_logs():
    """Read logs from the bot process."""
    global bot_process, bot_logs

    if bot_process is None or bot_process.stdout is None:
        return

    try:
        for line in bot_process.stdout:
            # Add the line to the logs
            bot_logs.append(line.strip())

            # Trim logs if they exceed the maximum
            if len(bot_logs) > MAX_LOGS:
                bot_logs = bot_logs[-MAX_LOGS:]
    except Exception:
        pass

def get_bot_logs(limit: int = 100):
    """Get the most recent bot logs."""
    global bot_logs

    # Return the most recent logs
    return bot_logs[-limit:] if bot_logs else []

def get_bot_settings():
    """Get the current bot settings."""
    # Convert absolute path to relative path for display
    project_root = os.getcwd()
    rel_bot_dir = os.path.relpath(os.path.abspath(BOT_DIR), project_root)

    # Use ./ prefix for relative paths in the current directory
    if not rel_bot_dir.startswith('..'):
        rel_bot_dir = './' + rel_bot_dir

    return {
        "bot_dir": rel_bot_dir,
        "bot_script": BOT_SCRIPT,
        "bot_venv": BOT_VENV,
        "bot_install_path": BOT_INSTALL_PATH,
        "editable_files": get_editable_files()
    }

def update_bot_settings(bot_script, bot_install_path=None, editable_files=None):
    """Update the bot settings."""
    # Update the .env file with the new bot script
    _update_env_file(bot_script)

    # Update the bot install path if provided
    if bot_install_path is not None:
        # Update the global variable
        global BOT_INSTALL_PATH
        BOT_INSTALL_PATH = bot_install_path

        # Update the .env file with the new bot install path
        env_path = ".env"

        # Read the current .env file
        with open(env_path, "r") as f:
            lines = f.readlines()

        # Update the BOT_INSTALL_PATH line or add it if it doesn't exist
        found = False
        updated_lines = []
        for line in lines:
            if line.startswith("BOT_INSTALL_PATH="):
                updated_lines.append(f"BOT_INSTALL_PATH={bot_install_path}\n")
                found = True
            else:
                updated_lines.append(line)

        # Add the line if it doesn't exist
        if not found:
            updated_lines.append(f"BOT_INSTALL_PATH={bot_install_path}\n")

        # Write the updated .env file
        with open(env_path, "w") as f:
            f.writelines(updated_lines)

    # Update editable files if provided
    if editable_files is not None:
        # Update the global variable in the editable_files module
        update_editable_files(editable_files)

        # Update the .env file with the new editable files
        env_path = ".env"

        # Read the current .env file
        with open(env_path, "r") as f:
            lines = f.readlines()

        # Update the EDITABLE_FILES line or add it if it doesn't exist
        editable_files_str = ",".join(editable_files)
        editable_files_line = f"EDITABLE_FILES={editable_files_str}\n"

        found = False
        updated_lines = []
        for line in lines:
            if line.startswith("EDITABLE_FILES="):
                updated_lines.append(editable_files_line)
                found = True
            else:
                updated_lines.append(line)

        # Add the line if it doesn't exist
        if not found:
            updated_lines.append(editable_files_line)

        # Write the updated .env file
        with open(env_path, "w") as f:
            f.writelines(updated_lines)

    # Return the updated settings
    return get_bot_settings()

def install_requirements():
    """Install requirements from requirements.txt in the bot's virtual environment."""
    try:
        # Get absolute paths
        abs_bot_dir = os.path.abspath(BOT_DIR)

        # Ensure bot directory exists
        os.makedirs(abs_bot_dir, exist_ok=True)

        # Check if requirements.txt exists
        requirements_path = os.path.join(abs_bot_dir, "requirements.txt")
        if not os.path.exists(requirements_path):
            return {
                "status": "error",
                "error": "Requirements file not found. Please create a requirements.txt file in the bot directory."
            }

        # Determine the correct pip path based on OS
        pip_path = "bin/pip" if os.name != "nt" else "Scripts\\pip.exe"
        venv_path = os.path.join(abs_bot_dir, BOT_VENV)
        venv_pip = os.path.join(venv_path, pip_path)

        # Check if the virtual environment exists
        if not os.path.exists(venv_path):
            # Create virtual environment if it doesn't exist
            try:
                print(f"Creating virtual environment at {venv_path}")
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("Virtual environment created successfully")
            except subprocess.CalledProcessError as e:
                return {
                    "status": "error",
                    "error": f"Failed to create virtual environment: {e.stderr}"
                }

        # Check again if pip exists after creating the virtual environment
        if not os.path.exists(venv_pip):
            # Try to find pip in the virtual environment
            if os.name != "nt":
                possible_pip_paths = [
                    os.path.join(venv_path, "bin", "pip"),
                    os.path.join(venv_path, "bin", "pip3")
                ]
            else:
                possible_pip_paths = [
                    os.path.join(venv_path, "Scripts", "pip.exe"),
                    os.path.join(venv_path, "Scripts", "pip3.exe")
                ]

            for path in possible_pip_paths:
                if os.path.exists(path):
                    venv_pip = path
                    break
            else:
                return {
                    "status": "error",
                    "error": "Pip not found in the virtual environment. Please check your Python installation."
                }

        # Install requirements
        try:
            print(f"Installing requirements from {requirements_path} using {venv_pip}")
            result = subprocess.run(
                [venv_pip, "install", "-r", requirements_path],
                check=True,
                capture_output=True,
                text=True,
                cwd=abs_bot_dir
            )

            return {
                "status": "success",
                "message": "Requirements installed successfully",
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": f"Failed to install requirements: {e.stderr}"
            }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
