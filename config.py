import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    if not os.environ.get("SECRET_KEY"):
        logger.warning(
            "SECRET_KEY not set — using a random key. Sessions will reset on restart. "
            "Set SECRET_KEY in your .env file for production."
        )

    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join("app", "database", "database.db"))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join("uploads", "resumes"))
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)
    )  # 100 MB default

    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Notifications
    HR_ALERT_EMAIL = os.environ.get("HR_ALERT_EMAIL", "")


os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)