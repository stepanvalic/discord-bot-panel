import os
import sys
import uvicorn
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if .env file exists, create if not
if not os.path.exists('.env'):
    print("Creating .env file...")

    # Generate a secret key
    secret_key = secrets.token_hex(32)

    # Create .env file with default values
    with open('.env', 'w') as f:
        f.write(f"# FastAPI settings\n")
        f.write(f"SECRET_KEY={secret_key}\n")
        f.write(f"ALGORITHM=HS256\n")
        f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES=30\n\n")

        f.write(f"# Bot settings\n")
        f.write(f"BOT_DIR=./workspace\n")
        f.write(f"BOT_SCRIPT=bot.py\n")
        f.write(f"BOT_VENV=venv\n\n")

        f.write(f"# Webhook settings\n")
        f.write(f"WEBHOOK_SECRET={secrets.token_urlsafe(16)}\n\n")

        f.write(f"# File editor settings\n")
        f.write(f"WHITELISTED_FILES=.env,config.yaml,config.json\n")

    print("Created .env file with default values.")

def main():
    # Run the FastAPI application
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
