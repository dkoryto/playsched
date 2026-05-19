import os
import sys
import tempfile

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set env vars BEFORE importing project modules that read them at import time
from cryptography.fernet import Fernet  # noqa: E402
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SPOTIPY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIPY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://localhost:9093/callback")
os.environ.setdefault("REQUIRE_PANEL_PASSWORD", "0")

test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.environ["SCHEDULE_DB_FILE"] = test_db_path

import pytest  # noqa: E402
from playsched import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    _app = create_app()
    _app.config.update({
        "TESTING": True,
    })
    yield _app
    os.close(test_db_fd)
    os.unlink(test_db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()
