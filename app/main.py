import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database initialization
from app.db.database import init_db

# Create FastAPI app
app = FastAPI(
    title="Discord Bot Panel",
    description="A web panel for managing a Discord bot",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
import os

# Ensure static directory exists
static_dir = "app/static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    # Create css and js subdirectories
    os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

# Ensure bot directory exists
bot_dir = "app/bot"
if not os.path.exists(bot_dir):
    os.makedirs(bot_dir)
    # Create __init__.py to make it a proper package
    with open(os.path.join(bot_dir, "__init__.py"), "w") as f:
        f.write("# Bot management package\n")

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Ensure templates directory exists
templates_dir = "app/templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Configure templates
templates = Jinja2Templates(directory=templates_dir)

# Import and include routers
from app.api.bot import router as bot_router
from app.api.ssh import router as ssh_router
from app.api.webhook import router as webhook_router
from app.api.files import router as files_router
from app.api.users import router as users_router
from app.api.env import router as env_router
from app.auth.router import router as auth_router

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(bot_router, prefix="/api/bot", tags=["Bot Management"])
app.include_router(ssh_router, prefix="/api/ssh-keys", tags=["SSH Keys"])
app.include_router(webhook_router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(files_router, prefix="/api/files", tags=["File Editor"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(env_router, prefix="/api/env", tags=["Environment"])

# Startup event to initialize database and scheduler
@app.on_event("startup")
async def startup_event():
    await init_db()

    # Initialize scheduler
    from app.utils.scheduler import init_scheduler
    init_scheduler()

# Login endpoint
@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Root endpoint
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Bot settings endpoint
@app.get("/bot-settings")
async def bot_settings(request: Request):
    return templates.TemplateResponse("bot_settings.html", {"request": request})

# SSH keys endpoint
@app.get("/ssh-keys")
async def ssh_keys(request: Request):
    return templates.TemplateResponse("ssh_keys.html", {"request": request})

# Webhook endpoint
@app.get("/webhook")
async def webhook(request: Request):
    return templates.TemplateResponse("webhook.html", {"request": request})

# Files endpoint
@app.get("/files")
async def files(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})

# Users endpoint
@app.get("/users")
async def users(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

# Environment endpoint
@app.get("/env")
async def env(request: Request):
    return templates.TemplateResponse("env.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
