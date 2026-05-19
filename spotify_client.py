import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import logging
from flask import session

import database
from config import Config

logger = logging.getLogger(__name__)

WEB_SCOPES = (
    "user-read-playback-state user-modify-playback-state playlist-read-private "
    "playlist-read-collaborative user-read-private user-read-email "
    "user-read-currently-playing user-read-recently-played"
)

print(f"SpotifyOAuth initialized with redirect_uri: {Config.SPOTIPY_REDIRECT_URI}")


class SpotifyAuthManager:
    """Encapsulates Spotify OAuth configuration and token operations."""

    def __init__(self):
        self.client_id = Config.SPOTIPY_CLIENT_ID
        self.client_secret = Config.SPOTIPY_CLIENT_SECRET
        self.redirect_uri = Config.SPOTIPY_REDIRECT_URI

    def _get_auth_manager(self) -> SpotifyOAuth:
        """Returns a SpotifyOAuth instance without file cache."""
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=WEB_SCOPES,
            open_browser=False,
        )

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refreshes a Spotify access token using the refresh token."""
        return self._get_auth_manager().refresh_access_token(refresh_token)

    def get_auth_url(self) -> str:
        """Gets the Spotify authorization URL."""
        return self._get_auth_manager().get_authorize_url()

    def get_token_from_code(self, code: str) -> bool:
        """Exchanges authorization code for tokens and stores them in the database."""
        try:
            auth_manager = self._get_auth_manager()
            token_info = auth_manager.get_access_token(code, check_cache=False)
            sp = spotipy.Spotify(auth=token_info["access_token"])
            user_info = sp.current_user()
            user_id = user_info["id"]
            session["spotify_user_id"] = user_id
            session["spotify_user_display_name"] = user_info.get("display_name", user_id)
            database.save_user_token(user_id, token_info)
            return True
        except Exception as e:
            logger.error(f"Error getting token from code: {e}")
            return False

    def get_refreshed_token(self, user_id: str | None = None) -> dict | None:
        """Checks if token needs refresh, refreshes if needed, returns token_info."""
        if user_id is None:
            user_id = session.get("spotify_user_id")
        if not user_id:
            return None

        token_info = database.get_user_token(user_id)
        if not token_info:
            return None

        now = int(time.time())
        is_expired = token_info["expires_at"] - now < 60  # Refresh if expires in < 60 seconds

        if is_expired:
            try:
                token_info = self.refresh_access_token(token_info["refresh_token"])
                database.save_user_token(user_id, token_info)
                logger.info(f"Spotify token refreshed for user {user_id}.")
            except Exception as e:
                logger.error(f"Error refreshing token for user {user_id}: {e}")
                database.delete_user_token(user_id)
                session.pop("spotify_user_id", None)
                session.pop("spotify_user_display_name", None)
                return None
        return token_info

    def get_spotify_client(self) -> spotipy.Spotify | None:
        """Returns an authenticated Spotipy client instance using DB-stored token."""
        token_info = self.get_refreshed_token()
        if not token_info:
            return None
        try:
            return spotipy.Spotify(auth=token_info["access_token"])
        except Exception as e:
            logger.error(f"Error creating spotipy client: {e}")
            return None

    def get_spotify_client_for_user(self, user_id: str) -> spotipy.Spotify | None:
        """Returns an authenticated Spotipy client for a specific user_id (no Flask session needed)."""
        token_info = self.get_refreshed_token(user_id=user_id)
        if not token_info:
            return None
        try:
            return spotipy.Spotify(auth=token_info["access_token"])
        except Exception as e:
            logger.error(f"Error creating spotipy client for user {user_id}: {e}")
            return None


# Global instance for backward compatibility
_default_auth_manager = SpotifyAuthManager()


def refresh_access_token(refresh_token: str) -> dict:
    """Refreshes a Spotify access token using the refresh token."""
    return _default_auth_manager.refresh_access_token(refresh_token)


def get_auth_url() -> str:
    """Gets the Spotify authorization URL."""
    return _default_auth_manager.get_auth_url()


def get_token_from_code(code: str) -> bool:
    """Exchanges authorization code for tokens and stores them in the database."""
    return _default_auth_manager.get_token_from_code(code)


def get_refreshed_token(user_id: str | None = None) -> dict | None:
    """Checks if token needs refresh, refreshes if needed, returns token_info."""
    return _default_auth_manager.get_refreshed_token(user_id=user_id)


def get_spotify_client() -> spotipy.Spotify | None:
    """Returns an authenticated Spotipy client instance using DB-stored token."""
    return _default_auth_manager.get_spotify_client()


def get_spotify_client_for_user(user_id: str) -> spotipy.Spotify | None:
    """Returns an authenticated Spotipy client for a specific user_id (no Flask session needed)."""
    return _default_auth_manager.get_spotify_client_for_user(user_id)


# --- Wrapper functions for API calls ---


def get_all_user_playlists(sp):
    """Gets ALL playlists for the current user using pagination internally."""
    if not sp:
        return None
    all_playlists = []
    offset = 0
    limit = 50  # Fetch 50 at a time (max)
    while True:
        try:
            results = sp.current_user_playlists(limit=limit, offset=offset)
            if not results or not results["items"]:
                break  # No more items
            all_playlists.extend(results["items"])
            if results["next"]:
                offset += limit
            else:
                break  # No more pages
        except spotipy.exceptions.SpotifyException as e:
            logger.error(
                f"Spotify API error fetching playlists page (offset={offset}): {e.msg}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching user playlists page (offset={offset}): {e}")
            return None
    logger.info(f"Fetched a total of {len(all_playlists)} playlists.")
    return all_playlists


def start_playback(sp, device_id, playlist_uri, volume=None):
    """Starts playlist playback on a device, optionally sets volume."""
    if not sp:
        return False
    try:
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        logger.info(f"Playback started: {playlist_uri} on {device_id}")
        if volume is not None and isinstance(volume, int) and 0 <= volume <= 100:
            time.sleep(1)
            try:
                sp.volume(volume, device_id=device_id)
                logger.info(f"Volume set to {volume} on {device_id}")
            except Exception as vol_e:
                logger.warning(f"Could not set volume after starting playback: {vol_e}")
        return True
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        return False


def stop_playback(sp, device_id):
    """Stops playback on a specific device."""
    if not sp:
        return False
    try:
        sp.pause_playback(device_id=device_id)
        logger.info(f"Playback paused (stopped) on device {device_id}")
        return True
    except Exception as e:
        logger.error(f"Error pausing playback on {device_id}: {e}")
        return False


def get_user_devices(sp):
    """Gets available playback devices for the current user."""
    if not sp:
        logger.error("get_user_devices called without valid sp client")
        return None
    try:
        devices_info = sp.devices()
        if devices_info and isinstance(devices_info.get("devices"), list):
            return devices_info["devices"]
        else:
            logger.warning(
                f"sp.devices() returned unexpected structure or no devices list: {devices_info}"
            )
            return []
    except spotipy.exceptions.SpotifyException as e:
        logger.error(
            f"Spotify API error fetching devices: {e.msg} (HTTP Status: {e.http_status})"
        )
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching user devices: {e}", exc_info=True)
        return None
