import os
import secrets
import asyncio
import logging
import logging.handlers
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, Cookie, Response, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.api.router import api_router
from app.auth.router import auth_router
from app.webhooks.router import webhook_router
from app.db.session import engine, Base, get_db
from app.auth.dependencies import get_current_user, get_current_user_from_session
from app.models.user import User
from app.models.ip_ban import IPBan
from app.utils.security import verify_password, get_password_hash
from app.utils.background_tasks import status_update_task
from app.utils.avatar_background_task import update_avatars_task
from app.db.migrate import run_migrations

# Setup logging
os.makedirs("logs", exist_ok=True)

# Configure panel logger
panel_logger = logging.getLogger("discord-bot-panel")
panel_logger.setLevel(logging.INFO)

# Create a formatter that includes hour and minute
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M')

# Create a file handler for the panel logs
panel_file_handler = logging.handlers.RotatingFileHandler(
    "logs/panel.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
panel_file_handler.setFormatter(log_formatter)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Add the handlers to the logger
panel_logger.addHandler(panel_file_handler)
panel_logger.addHandler(console_handler)

# Configure bot logger
bot_logger = logging.getLogger("bot")
bot_logger.setLevel(logging.INFO)

# Create a file handler for the bot logs
bot_file_handler = logging.handlers.RotatingFileHandler(
    "logs/bot.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
bot_file_handler.setFormatter(log_formatter)
bot_logger.addHandler(bot_file_handler)
bot_logger.addHandler(console_handler)

# Create the FastAPI app
app = FastAPI(
    title="Discord Bot Panel",
    description="A web panel for managing a Discord bot",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
import os
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])

# Create database tables
Base.metadata.create_all(bind=engine)

# Run database migrations
run_migrations()

# Ensure work-bot directory exists
os.makedirs("work-bot", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    # Start the status update task
    asyncio.create_task(status_update_task())

    # Start the avatar update task
    asyncio.create_task(update_avatars_task())


@app.get("/")
async def root(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Root endpoint that redirects to the dashboard
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user}
    )


@app.get("/git")
async def git_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Git repository management page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "git.html", {"request": request, "user": user}
    )


@app.get("/webhook")
async def webhook_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Webhook page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "webhook.html", {"request": request, "user": user}
    )


@app.get("/files")
async def files_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Files page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "files.html", {"request": request, "user": user}
    )


@app.get("/env")
async def env_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Environment variables page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "env.html", {"request": request, "user": user}
    )


@app.get("/requirements")
async def requirements_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Requirements page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "requirements.html", {"request": request, "user": user}
    )


@app.get("/system")
async def system_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    System dependencies page
    """
    if not user:
        return RedirectResponse(url="/login")

    # Check if user is admin
    if user.role != "admin":
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "system.html", {"request": request, "user": user}
    )


@app.get("/discord")
async def discord_settings_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Discord settings page
    """
    if not user:
        return RedirectResponse(url="/login")

    # Check if user is admin
    if user.role != "admin":
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "discord_settings.html", {"request": request, "user": user}
    )


@app.get("/ip-bans")
async def ip_bans_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    IP Bans page
    """
    if not user:
        return RedirectResponse(url="/login")

    # Check if user is admin
    if user.role != "admin":
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "ip_bans.html", {"request": request, "user": user}
    )


@app.get("/token-usage")
async def token_usage_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Token usage page - accessible to all users
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "token_usage.html", {"request": request, "user": user}
    )


@app.get("/users")
async def users_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    Users management page
    """
    if not user:
        return RedirectResponse(url="/login")

    # Check if user is admin
    if user.role != "admin":
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "users.html", {"request": request, "user": user}
    )


@app.get("/profile")
async def profile_page(request: Request, user: User = Depends(get_current_user_from_session)):
    """
    User profile page
    """
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user}
    )


@app.post("/profile")
async def update_profile(request: Request,
                       discord_id: str = Form(None),
                       avatar_url: str = Form(None),
                       password: str = Form(None),
                       confirm_password: str = Form(None),
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user_from_session)):
    """
    Update user profile
    """
    if not current_user:
        return RedirectResponse(url="/login")

    # Get the user from the database
    user = db.query(User).filter(User.id == current_user.id).first()

    # Check if another user already has this Discord ID
    if discord_id and discord_id.strip():
        existing_user = db.query(User).filter(User.discord_id == discord_id, User.id != user.id).first()
        if existing_user:
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "user": user, "message": "This Discord ID is already in use", "success": False}
            )
        user.discord_id = discord_id.strip()
    elif discord_id == "":
        # If the field was cleared, set to None
        user.discord_id = None

    # Update avatar URL
    if avatar_url and avatar_url.strip():
        user.avatar_url = avatar_url.strip()
    elif avatar_url == "":
        # If the field was cleared, set to None
        user.avatar_url = None

    # Update password if provided
    if password and password.strip():
        if password != confirm_password:
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "user": user, "message": "Passwords do not match", "success": False}
            )

        if len(password) < 8:
            return templates.TemplateResponse(
                "profile.html",
                {"request": request, "user": user, "message": "Password must be at least 8 characters", "success": False}
            )

        user.password_hash = get_password_hash(password)

    # Save changes
    db.commit()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "message": "Profile updated successfully", "success": True}
    )


@app.get("/login")
async def login_page(request: Request, session: str = Cookie(None)):
    """
    Login page
    """
    # Check if user is already logged in
    if session:
        from app.auth.dependencies import SESSION_STORE
        if session in SESSION_STORE:
            return RedirectResponse(url="/")

    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Process login form
    """
    # Get client IP address
    client_ip = request.client.host
    panel_logger.info(f"Login attempt from IP: {client_ip}, username: {username}")

    # Check if IP is banned
    ip_ban = db.query(IPBan).filter(IPBan.ip_address == client_ip).first()
    if ip_ban and ip_ban.is_banned:
        panel_logger.warning(f"Blocked login attempt from banned IP: {client_ip}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Your IP address has been banned due to too many failed login attempts."},
            status_code=403
        )

    # Authenticate the user
    try:
        user = db.query(User).filter(User.username == username).first()
    except Exception as e:
        # Handle the case where the discord_id column doesn't exist yet
        if "no such column: users.discord_id" in str(e):
            # Use a more basic query that doesn't include the discord_id column
            user = db.query(User.id, User.username, User.password_hash, User.role, User.first_login).filter(User.username == username).first()
        else:
            raise

    if not user or not verify_password(password, user.password_hash):
        # Record failed login attempt
        if not ip_ban:
            # Create new IP ban record
            ip_ban = IPBan(ip_address=client_ip, failed_attempts=1)
            db.add(ip_ban)
        else:
            # Increment failed attempts
            ip_ban.failed_attempts += 1
            ip_ban.last_attempt_at = datetime.now()

            # Ban IP after 3 failed attempts
            if ip_ban.failed_attempts >= 3 and not ip_ban.is_banned:
                ip_ban.is_banned = True
                ip_ban.banned_at = datetime.now()
                panel_logger.warning(f"IP address banned due to too many failed login attempts: {client_ip}")

        db.commit()

        # Return error message
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=400
        )

    # Reset failed login attempts on successful login
    if ip_ban:
        ip_ban.failed_attempts = 0
        db.commit()

    # Create a session
    from app.auth.dependencies import SESSION_STORE
    session_id = secrets.token_hex(16)
    SESSION_STORE[session_id] = {"user_id": user.id}

    # Set the session cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="session", value=session_id, httponly=True)

    # If this is the first login, mark it as completed
    if user.first_login:
        user.first_login = False
        db.commit()

    panel_logger.info(f"Successful login for user: {username} from IP: {client_ip}")
    return response


@app.get("/register")
async def register_page(request: Request):
    """
    Registration page - only available if no users exist
    """
    db = next(get_db())
    user_count = db.query(User).count()

    if user_count > 0:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Process registration form
    """
    # Check if any users exist
    user_count = db.query(User).count()

    if user_count > 0:
        return RedirectResponse(url="/login", status_code=303)

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"},
            status_code=400
        )

    # Create new user with admin role (first user)
    hashed_password = get_password_hash(password)
    try:
        db_user = User(
            username=username,
            password_hash=hashed_password,
            role="admin",
            first_login=False,
        )
    except Exception as e:
        # If there's an error with the discord_id column, create a user without it
        if "discord_id" in str(e):
            # Create a dictionary with only the fields we know exist
            user_data = {
                "username": username,
                "password_hash": hashed_password,
                "role": "admin",
                "first_login": False
            }
            db_user = User(**user_data)
        else:
            raise

    db.add(db_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)


@app.get("/logout")
async def logout(response: Response):
    """
    Logout and clear session
    """
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="session")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
