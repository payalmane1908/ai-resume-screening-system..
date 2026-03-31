import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "database.db")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    # Increase request payload cap for bulk resume uploads.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))  # 100 MB default


os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)