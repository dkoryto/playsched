import re
import pytz


def validate_schedule_payload(data: dict, partial: bool = False) -> tuple[bool, str | None]:
    """Validates schedule create/update payload.

    Args:
        data (dict): The payload to validate.
        partial (bool): If True, allows missing fields (for updates).

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    required = [
        "playlist_uri",
        "target_device_id",
        "days_of_week",
        "start_time_local",
        "timezone",
    ]

    if not partial:
        missing = [f for f in required if f not in data]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

    # playlist_uri
    if "playlist_uri" in data:
        uri = data["playlist_uri"]
        if not isinstance(uri, str) or not uri.strip():
            return False, "playlist_uri must be a non-empty string"
        if not uri.startswith("spotify:"):
            return False, "playlist_uri must be a valid Spotify URI"

    # target_device_id
    if "target_device_id" in data:
        device = data["target_device_id"]
        if not isinstance(device, str) or not device.strip():
            return False, "target_device_id must be a non-empty string"

    # days_of_week
    if "days_of_week" in data:
        days = data["days_of_week"]
        if not isinstance(days, str):
            return False, "days_of_week must be a string"
        if days.strip() != "":
            try:
                day_set = {int(d.strip()) for d in days.split(",") if d.strip() != ""}
            except ValueError:
                return False, "days_of_week must be comma-separated integers 0-6"
            if not day_set.issubset(set(range(7))):
                return False, "days_of_week values must be between 0 and 6"

    # start_time_local / stop_time_local
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    for field in ("start_time_local", "stop_time_local"):
        if field in data and data[field] is not None:
            val = data[field]
            if not isinstance(val, str) or not time_pattern.match(val):
                return False, f"{field} must be in HH:MM format"
            try:
                h, m = map(int, val.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except ValueError:
                return False, f"{field} contains invalid time values"

    # timezone
    if "timezone" in data:
        tz = data["timezone"]
        if not isinstance(tz, str) or not tz.strip():
            return False, "timezone must be a non-empty string"
        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            return False, f"timezone '{tz}' is not recognized"

    # volume
    if "volume" in data and data["volume"] is not None:
        vol = data["volume"]
        if not isinstance(vol, int) or not (0 <= vol <= 100):
            return False, "volume must be an integer between 0 and 100"

    # shuffle_state
    if "shuffle_state" in data:
        if not isinstance(data["shuffle_state"], bool):
            return False, "shuffle_state must be a boolean"

    # is_active
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return False, "is_active must be a boolean"

    return True, None


def validate_playback_payload(data: dict) -> tuple[bool, str | None]:
    """Validates arbitrary playback request payload."""
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    if "playlist_uri" not in data or "device_id" not in data:
        return False, "Missing required fields: playlist_uri, device_id"

    uri = data["playlist_uri"]
    if not isinstance(uri, str) or not uri.strip() or not uri.startswith("spotify:"):
        return False, "playlist_uri must be a valid Spotify URI"

    device = data["device_id"]
    if not isinstance(device, str) or not device.strip():
        return False, "device_id must be a non-empty string"

    if "volume" in data and data["volume"] is not None:
        vol = data["volume"]
        if not isinstance(vol, int) or not (0 <= vol <= 100):
            return False, "volume must be an integer between 0 and 100"

    return True, None
