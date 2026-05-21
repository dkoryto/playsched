import logging
import sys
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, redirect, request, session, url_for

import atexit

import scheduler as scheduler_module
from config import Config
from extensions import limiter
from routes import main_bp, api_bp


def setup_logging(app: Flask) -> None:
    """Configures application logging with optional rotating file handler."""
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(log_level)

    # Rotating file handler
    if Config.LOG_FILE:
        try:
            file_handler = RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=Config.LOG_MAX_BYTES,
                backupCount=Config.LOG_BACKUP_COUNT,
            )
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
        except Exception as e:
            app.logger.warning(f"Could not set up log file {Config.LOG_FILE}: {e}")


def create_app() -> Flask:
    """Application factory pattern for creating the Flask app."""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    # Initialize extensions
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Logging
    setup_logging(app)

    # Error handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Rate limit exceeded", "retry_after": str(e.description)}), 429

    # Panel password gate (before Spotify auth)
    @app.before_request
    def panel_auth_gate():
        if not Config.REQUIRE_PANEL_PASSWORD or not request.endpoint:
            return None
        exempt_endpoints = {
            "static",
            "main.index",
            "api.api_panel_login",
            "api.api_panel_auth_status",
            "api.api_health",
            "api.api_set_language",
        }
        if request.endpoint in exempt_endpoints:
            return None
        if session.get("panel_authenticated") is True:
            return None
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Panel password required", "needs_panel_auth": True}), 403
        return redirect(url_for("main.index"))

    # Auth gate for API (before_request on blueprint runs after app-level)
    @app.before_request
    def before_request_hook():
        if (
            request.endpoint
            and "api." in request.endpoint
            and request.endpoint not in ["api.api_auth_status", "api.api_health", "api.api_set_language", "api.api_panel_login", "api.api_panel_auth_status"]
        ):
            if "spotify_user_id" not in session:
                return jsonify({"error": "User not authenticated"}), 401

    # Initialize scheduler
    background_scheduler = BackgroundScheduler(daemon=True)
    background_scheduler.add_job(
        func=scheduler_module.check_schedules,
        args=[app.logger],
        trigger="interval",
        seconds=Config.SCHEDULER_INTERVAL_SECONDS,
        id="schedule_check_job",
    )
    background_scheduler.start()
    atexit.register(lambda: background_scheduler.shutdown())

    app.logger.info("Flask application created and scheduler started.")
    return app
