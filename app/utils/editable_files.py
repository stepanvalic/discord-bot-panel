import os
from dotenv import load_dotenv

# Global variable to store the current list of editable files
_EDITABLE_FILES = []

def load_editable_files():
    """Load the list of editable files from the environment variables."""
    global _EDITABLE_FILES
    
    # Reload environment variables
    load_dotenv()
    
    # Get the list of editable files
    editable_files_str = os.getenv("EDITABLE_FILES", ".env,config.json,config.yaml,config.yml")
    
    # Split the string into a list and clean it up
    _EDITABLE_FILES = [pattern.strip() for pattern in editable_files_str.split(",") if pattern.strip()]
    
    return _EDITABLE_FILES

def get_editable_files():
    """Get the current list of editable files."""
    global _EDITABLE_FILES
    
    # If the list is empty, load it
    if not _EDITABLE_FILES:
        load_editable_files()
    
    return _EDITABLE_FILES

def update_editable_files(editable_files):
    """Update the list of editable files."""
    global _EDITABLE_FILES
    
    # Update the global variable
    _EDITABLE_FILES = editable_files
    
    return _EDITABLE_FILES

def is_file_editable(file_path):
    """Check if a file is editable."""
    # Get the file name
    file_name = os.path.basename(file_path)
    
    # Get the current list of editable files
    editable_files = get_editable_files()
    
    # Check if the file is in the editable files list
    for pattern in editable_files:
        # Check for exact match
        if file_name == pattern:
            return True
        
        # Check for wildcard match (e.g., *.json)
        if pattern.startswith('*.'):
            extension = pattern[1:]  # Remove the '*'
            if file_name.endswith(extension):
                return True
    
    return False

# Initialize the list of editable files
load_editable_files()
