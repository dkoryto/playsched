import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from flask import session  # Keep session for user_id/display_name only
import time
import logging

import database

logger = logging.getLogger(__name__)

load_dotenv()

WEB_SCOPES = (
    "user-read-playback-state user-modify-playback-state playlist-read-private "
    "playlist-read-collaborative user-read-private user-read-email "
    "user-read-currently-playing user-read-recently-played"
)

_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

print(f"SpotifyOAuth initialized with redirect_uri: {_REDIRECT_URI}")


def _get_auth_manager():
    """Returns a SpotifyOAuth instance without file cache."""
    return SpotifyOAuth(
        client_id=_CLIENT_ID,
        client_secret=_CLIENT_SECRET,
        redirect_uri=_REDIRECT_URI,
        scope=WEB_SCOPES,
        open_browser=False,
    )


def get_auth_url():
    """Gets the Spotify authorization URL."""
    return _get_auth_manager().get_authorize_url()


def get_token_from_code(code):
    """Exchanges authorization code for tokens and stores them in the database."""
    try:
        auth_manager = _get_auth_manager()
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


def get_refreshed_token(user_id=None):
    """Checks if token needs refresh, refreshes if needed, returns token_info."""
    if user_id is None:
        user_id = session.get("spotify_user_id")
    if not user_id:
        return None

    token_info = database.get_user_token(user_id)
    if not token_info:
        return None

    now = int(time.time())
    is_expired = (
        token_info["expires_at"] - now < 60
    )  # Refresh if expires in < 60 seconds

    if is_expired:
        try:
            auth_manager = _get_auth_manager()
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            database.save_user_token(user_id, token_info)
            logger.info(f"Spotify token refreshed for user {user_id}.")
        except Exception as e:
            logger.error(f"Error refreshing token for user {user_id}: {e}")
            database.delete_user_token(user_id)
            session.pop("spotify_user_id", None)
            session.pop("spotify_user_display_name", None)
            return None
    return token_info


def get_spotify_client():
    """Returns an authenticated Spotipy client instance using DB-stored token."""
    token_info = get_refreshed_token()
    if not token_info:
        return None
    try:
        return spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        logger.error(f"Error creating spotipy client: {e}")
        return None


def get_spotify_client_for_user(user_id):
    """Returns an authenticated Spotipy client for a specific user_id (no Flask session needed)."""
    token_info = get_refreshed_token(user_id=user_id)
    if not token_info:
        return None
    try:
        return spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        logger.error(f"Error creating spotipy client for user {user_id}: {e}")
        return None


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
