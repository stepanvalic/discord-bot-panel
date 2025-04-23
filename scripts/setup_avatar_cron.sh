#!/bin/bash

# Script to set up a cron job for updating Discord avatars
# This script should be run as the user who will run the cron job

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/app/scripts/update_avatars.py"

# Make sure the script is executable
chmod +x "$SCRIPT_PATH"

# Create a temporary file for the cron job
TEMP_CRON=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# Discord Bot Panel Avatar Update Cron" > "$TEMP_CRON"

# Check if the cron job already exists
if grep -q "update_avatars.py" "$TEMP_CRON"; then
    echo "Cron job for avatar updates already exists."
else
    # Add the cron job to run every hour
    echo "# Run Discord avatar update every hour" >> "$TEMP_CRON"
    echo "0 * * * * cd $PROJECT_DIR && $SCRIPT_PATH >> $PROJECT_DIR/logs/avatar_cron.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    echo "Cron job for avatar updates has been added to run every hour."
fi

# Clean up
rm "$TEMP_CRON"

echo "Setup complete. Avatar updates will run every hour."
echo "You can check the logs at: $PROJECT_DIR/logs/avatar_cron.log"
