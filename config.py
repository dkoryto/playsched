import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "DEFAULT_FALLBACK_SECRET_KEY_CHANGE_ME")
    FLASK_RUN_HOST: str = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    FLASK_RUN_PORT: int = int(os.getenv("FLASK_RUN_PORT", "9093"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG") == "1"
    FLASK_CERT_FILE: str | None = os.getenv("FLASK_CERT_FILE")
    FLASK_KEY_FILE: str | None = os.getenv("FLASK_KEY_FILE")

    # Spotify
    SPOTIPY_CLIENT_ID: str | None = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET: str | None = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI: str | None = os.getenv("SPOTIPY_REDIRECT_URI")
    SPOTIPY_MARKET: str | None = os.getenv("SPOTIPY_MARKET")

    # Scheduler
    SCHEDULER_INTERVAL_SECONDS: int = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    SCHEDULER_LOCK_TTL_SECONDS: int = int(os.getenv("SCHEDULER_LOCK_TTL_SECONDS", "300"))

    # Database
    SCHEDULE_DB_FILE: str = os.getenv("SCHEDULE_DB_FILE", "playsched.db")

    # Security
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

    # i18n
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "pl")

    # Panel Password Protection
    PANEL_PASSWORD: str | None = os.getenv("PANEL_PASSWORD")
    REQUIRE_PANEL_PASSWORD: bool = os.getenv("REQUIRE_PANEL_PASSWORD", "0") == "1"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str | None = os.getenv("LOG_FILE")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "1048576"))  # 1 MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
