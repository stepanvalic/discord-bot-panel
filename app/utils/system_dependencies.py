import os
import subprocess
import logging
import platform

# Get logger
logger = logging.getLogger("discord-bot-panel")

def check_system_dependencies():
    """
    Check if the system has the required dependencies for the Discord bot
    Returns a tuple of (success, message)
    """
    logger.info("Checking system dependencies...")
    
    # Check the operating system
    system = platform.system()
    if system == "Linux":
        return check_linux_dependencies()
    elif system == "Windows":
        return check_windows_dependencies()
    elif system == "Darwin":  # macOS
        return check_macos_dependencies()
    else:
        return False, f"Unsupported operating system: {system}"

def check_linux_dependencies():
    """
    Check if the Linux system has the required dependencies
    Returns a tuple of (success, message)
    """
    missing_packages = []
    
    # Check for required packages
    packages = ["build-essential", "python3-dev", "libffi-dev", "libopus-dev", "ffmpeg"]
    
    for package in packages:
        try:
            # Check if the package is installed
            result = subprocess.run(
                ["dpkg", "-s", package],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                missing_packages.append(package)
        except Exception as e:
            logger.error(f"Error checking for package {package}: {e}")
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"Missing system packages: {', '.join(missing_packages)}. Please run 'sudo apt-get install {' '.join(missing_packages)}'"
    
    return True, "All system dependencies are installed"

def check_windows_dependencies():
    """
    Check if the Windows system has the required dependencies
    Returns a tuple of (success, message)
    """
    # Windows doesn't need additional system packages for basic functionality
    return True, "Windows doesn't require additional system packages"

def check_macos_dependencies():
    """
    Check if the macOS system has the required dependencies
    Returns a tuple of (success, message)
    """
    missing_packages = []
    
    # Check for required packages using Homebrew
    packages = ["opus", "ffmpeg"]
    
    for package in packages:
        try:
            # Check if the package is installed using Homebrew
            result = subprocess.run(
                ["brew", "list", package],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                missing_packages.append(package)
        except Exception as e:
            logger.error(f"Error checking for package {package}: {e}")
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"Missing system packages: {', '.join(missing_packages)}. Please run 'brew install {' '.join(missing_packages)}'"
    
    return True, "All system dependencies are installed"

def install_linux_dependencies():
    """
    Install the required system dependencies on Linux
    Returns a tuple of (success, message, log_lines)
    """
    log_lines = []
    
    try:
        # Update package list
        log_lines.append("Updating package list...")
        result = subprocess.run(
            ["sudo", "apt-get", "update"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        log_lines.append(result.stdout)
        
        # Install required packages
        packages = ["build-essential", "python3-dev", "libffi-dev", "libopus-dev", "ffmpeg"]
        log_lines.append(f"Installing packages: {' '.join(packages)}...")
        
        result = subprocess.run(
            ["sudo", "apt-get", "install", "-y"] + packages,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        log_lines.append(result.stdout)
        
        if result.returncode != 0:
            return False, "Failed to install system dependencies", log_lines
        
        return True, "System dependencies installed successfully", log_lines
    except Exception as e:
        logger.error(f"Error installing system dependencies: {e}")
        log_lines.append(f"Error: {e}")
        return False, f"Error installing system dependencies: {e}", log_lines
