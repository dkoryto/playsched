from datetime import datetime, time, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    current_app,
    make_response,
)

import translations as i18n_module
import pytz
import time as _time

import hmac

import database
import spotify_client
import validation
from config import Config
from extensions import limiter
from spotipy.exceptions import SpotifyException

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


# --- i18n Helpers ---

def _get_lang() -> str:
    """Read preferred language from cookie or fallback to DEFAULT_LANGUAGE."""
    lang = request.cookies.get("lang", Config.DEFAULT_LANGUAGE)
    return i18n_module._resolve_lang(lang)


def _t(key: str, **kwargs) -> str:
    """Shorthand for get_translation using the request language."""
    return i18n_module.get_translation(_get_lang(), key, **kwargs)


# --- Helpers ---

def calculate_next_play_time_utc(schedule: dict, now_utc: datetime) -> datetime | None:
    """Calculates the next run time for a schedule in UTC."""
    logger = current_app.logger if current_app else __import__("logging").getLogger(__name__)
    schedule_id_log = schedule.get("id", "N/A")

    logger.info(f"[Calc {schedule_id_log}]: --- Starting Calculation ---")

    if not isinstance(schedule, dict):
        logger.error(f"[Calc {schedule_id_log}]: Invalid schedule format. Returning None.")
        return None

    is_active_val = schedule.get("is_active")
    if not is_active_val:
        logger.info(f"[Calc {schedule_id_log}]: Returning None - Schedule inactive.")
        return None

    tz_str = schedule.get("timezone")
    start_time_str = schedule.get("start_time_local")
    days_of_week_str = schedule.get("days_of_week", "")
    is_play_once = days_of_week_str == ""
    play_once_triggered = schedule.get("play_once_triggered", False)

    if not tz_str or not start_time_str:
        logger.warning(f"[Calc {schedule_id_log}]: Returning None - Missing timezone or start_time_local.")
        return None

    if is_play_once and play_once_triggered:
        logger.info(f"[Calc {schedule_id_log}]: Returning None - Play-once triggered.")
        return None

    try:
        schedule_tz = pytz.timezone(tz_str)
        start_time_local_obj = time.fromisoformat(start_time_str)
        scheduled_days = set()
        if not is_play_once:
            if days_of_week_str:
                scheduled_days = {int(day) for day in days_of_week_str.split(",") if day.strip()}
            else:
                logger.warning(f"[Calc {schedule_id_log}]: Returning None - Repeating schedule has empty days_of_week.")
                return None
    except Exception as e:
        logger.error(f"[Calc {schedule_id_log}]: Returning None - Error parsing schedule data: {e}", exc_info=True)
        return None

    current_date_utc = now_utc.date()
    for i in range(8):
        check_date_utc = current_date_utc + timedelta(days=i)
        try:
            naive_potential_dt = datetime.combine(check_date_utc, start_time_local_obj)
        except Exception as combine_e:
            logger.error(f"[Calc {schedule_id_log}]: Error combining date/time: {combine_e}. Skipping day {i}.")
            continue

        try:
            localized_potential_dt = schedule_tz.localize(naive_potential_dt, is_dst=None)
        except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError) as loc_e:
            logger.warning(f"[Calc {schedule_id_log}]: Timezone localization issue: {loc_e}. Skipping.")
            continue
        except Exception as e:
            logger.error(f"[Calc {schedule_id_log}]: Error localizing time: {e}. Skipping day {i}.")
            continue

        potential_dt_utc = localized_potential_dt.astimezone(pytz.utc)
        potential_weekday_local = localized_potential_dt.weekday()

        is_scheduled_day = False
        if is_play_once:
            now_local_check = now_utc.astimezone(schedule_tz)
            if localized_potential_dt.date() == now_local_check.date():
                is_scheduled_day = True
            else:
                continue
        elif potential_weekday_local in scheduled_days:
            is_scheduled_day = True

        if not is_scheduled_day:
            continue

        if potential_dt_utc > now_utc:
            logger.info(f"[Calc {schedule_id_log}]: Found next future UTC time: {potential_dt_utc.isoformat()}.")
            return potential_dt_utc

    logger.warning(f"[Calc {schedule_id_log}]: Returning None - Could not find valid future run time within 7 days.")
    return None


# --- Main Routes ---

@main_bp.route("/")
def index():
    lang = _get_lang()
    i18n_data = i18n_module.get_all_translations(lang)
    ctx = {
        "logged_in": False,
        "lang": lang,
        "i18n": i18n_data,
        "available_langs": i18n_module.AVAILABLE_LANGUAGES,
        "language_names": i18n_module.LANGUAGE_NAMES,
    }
    if "spotify_user_id" in session:
        ctx["logged_in"] = True
        ctx["display_name"] = session.get("spotify_user_display_name", "User")
    return render_template("index.html", **ctx)


@main_bp.route("/login")
@limiter.limit("30 per minute")
def login():
    auth_url = spotify_client.get_auth_url()
    return redirect(auth_url)


@main_bp.route("/logout")
@limiter.limit("30 per minute")
def logout():
    session.pop("spotify_token_info", None)
    session.pop("spotify_user_id", None)
    session.pop("spotify_user_display_name", None)
    return redirect(url_for("main.index"))


@api_bp.route("/set_language", methods=["POST"])
@limiter.limit("60 per minute")
def api_set_language():
    data = request.json or {}
    lang = data.get("lang", Config.DEFAULT_LANGUAGE)
    lang = i18n_module._resolve_lang(lang)
    response = make_response(jsonify({"lang": lang}))
    response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


@main_bp.route("/callback")
@limiter.limit("10 per minute")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided in callback.", 400
    success = spotify_client.get_token_from_code(code)
    if success:
        return redirect(url_for("main.index"))
    else:
        return "Error: Could not fetch token from Spotify.", 500


# --- API Routes ---

@api_bp.route("/panel_auth_status", methods=["GET"])
@limiter.limit("60 per minute")
def api_panel_auth_status():
    if not Config.REQUIRE_PANEL_PASSWORD:
        return jsonify({"required": False, "authenticated": True}), 200
    return jsonify(
        {"required": True, "authenticated": session.get("panel_authenticated") is True}
    ), 200


@api_bp.route("/panel_logout", methods=["POST"])
@limiter.limit("30 per minute")
def api_panel_logout():
    session.pop("panel_authenticated", None)
    return jsonify({"success": True}), 200


@api_bp.route("/panel_login", methods=["POST"])
@limiter.limit("10 per minute")
def api_panel_login():
    if not Config.REQUIRE_PANEL_PASSWORD:
        return jsonify({"message": "Panel password not required"}), 200
    if not Config.PANEL_PASSWORD:
        return jsonify({"error": "Panel password not configured"}), 500

    data = request.json or {}
    provided = data.get("password", "")
    if hmac.compare_digest(provided, Config.PANEL_PASSWORD):
        session["panel_authenticated"] = True
        return jsonify({"success": True}), 200
    return jsonify({"error": "Invalid password"}), 401


@api_bp.route("/auth/status", methods=["GET"])
@limiter.limit("60 per minute")
def api_auth_status():
    if "spotify_user_id" in session and spotify_client.get_refreshed_token():
        return (
            jsonify(
                {
                    "logged_in": True,
                    "user_id": session["spotify_user_id"],
                    "display_name": session.get("spotify_user_display_name", "User"),
                }
            ),
            200,
        )
    else:
        session.pop("spotify_token_info", None)
        session.pop("spotify_user_id", None)
        session.pop("spotify_user_display_name", None)
        return jsonify({"logged_in": False}), 200


@api_bp.route("/playlists", methods=["GET"])
@limiter.limit("60 per minute")
def api_get_playlists():
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Authentication required or failed"}), 401
    try:
        playlists = spotify_client.get_all_user_playlists(sp)
        if playlists is None:
            return jsonify({"error": "Failed to fetch playlists from Spotify"}), 502
        playlist_data = [
            {"uri": p["uri"], "name": p["name"], "id": p["id"]} for p in playlists
        ]
        return jsonify(playlist_data), 200
    except Exception as e:
        current_app.logger.error(f"Error in /api/playlists endpoint: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@api_bp.route("/devices", methods=["GET"])
@limiter.limit("60 per minute")
def api_get_devices():
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Authentication required or failed"}), 401
    devices = spotify_client.get_user_devices(sp)
    if devices is None:
        return jsonify({"error": "Failed to fetch devices"}), 500
    device_data = [
        {
            "id": d["id"],
            "name": d["name"],
            "type": d["type"],
            "is_active": d["is_active"],
        }
        for d in devices
    ]
    return jsonify(device_data), 200


@api_bp.route("/schedules", methods=["GET"])
@limiter.limit("60 per minute")
def api_get_schedules():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    schedules = database.get_all_schedules(user_id)
    now_utc = datetime.now(pytz.utc)

    processed_schedules = []
    for schedule in schedules:
        next_time_obj = calculate_next_play_time_utc(schedule, now_utc)
        schedule["_next_play_time_utc_iso"] = next_time_obj.isoformat() if next_time_obj else None
        schedule["_sort_obj"] = next_time_obj
        processed_schedules.append(schedule)

    def sort_key(schedule):
        next_time = schedule.get("_sort_obj")
        return next_time if next_time else datetime.max.replace(tzinfo=pytz.utc)

    try:
        processed_schedules.sort(key=sort_key)
    except Exception as sort_e:
        current_app.logger.error(f"Error sorting schedules for user {user_id}: {sort_e}", exc_info=True)

    for schedule in processed_schedules:
        schedule.pop("_sort_obj", None)

    return jsonify(processed_schedules), 200


@api_bp.route("/schedules", methods=["POST"])
@limiter.limit("30 per minute")
def api_add_schedule():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    is_valid, error_msg = validation.validate_schedule_payload(data, partial=False)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    data["user_spotify_id"] = user_id
    data["shuffle_state"] = data.get("shuffle_state", False)
    schedule_id = database.add_schedule(data)

    if schedule_id:
        new_schedule = database.get_schedule_by_id(schedule_id, user_id)
        return jsonify(new_schedule), 201
    else:
        return jsonify({"error": "Failed to create schedule in database"}), 500


@api_bp.route("/schedules/<int:schedule_id>", methods=["PUT"])
@limiter.limit("30 per minute")
def api_update_schedule(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    is_valid, error_msg = validation.validate_schedule_payload(data, partial=True)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    if "shuffle_state" in data:
        data["shuffle_state"] = bool(data["shuffle_state"])

    success = database.update_schedule(schedule_id, user_id, data)
    if success:
        updated_schedule = database.get_schedule_by_id(schedule_id, user_id)
        return jsonify(updated_schedule), 200
    else:
        existing = database.get_schedule_by_id(schedule_id, user_id)
        if not existing:
            return jsonify({"error": "Schedule not found"}), 404
        else:
            return jsonify({"error": "Failed to update schedule"}), 500


@api_bp.route("/schedules/<int:schedule_id>", methods=["DELETE"])
@limiter.limit("30 per minute")
def api_delete_schedule(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    success = database.delete_schedule(schedule_id, user_id)
    if success:
        return jsonify({"message": "Schedule deleted successfully"}), 200
    else:
        existing = database.get_schedule_by_id(schedule_id, user_id)
        if not existing:
            return jsonify({"error": "Schedule not found"}), 404
        else:
            return jsonify({"error": "Failed to delete schedule"}), 500


@api_bp.route("/schedules/<int:schedule_id>/move", methods=["PUT"])
@limiter.limit("60 per minute")
def api_move_schedule(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json or {}
    direction = data.get("direction")
    if direction not in ("up", "down"):
        return jsonify({"error": "direction must be 'up' or 'down'"}), 400

    schedules = database.get_all_schedules(user_id)
    idx = next((i for i, s in enumerate(schedules) if s["id"] == schedule_id), -1)
    if idx == -1:
        return jsonify({"error": "Schedule not found"}), 404

    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(schedules):
        return jsonify({"error": "Cannot move further"}), 400

    success = database.swap_sort_order(schedule_id, schedules[swap_idx]["id"], user_id)
    if success:
        return jsonify({"message": f"Moved {direction}"}), 200
    return jsonify({"error": "Failed to move schedule"}), 500


@api_bp.route("/schedules/<int:schedule_id>/toggle", methods=["PUT"])
@limiter.limit("30 per minute")
def api_toggle_schedule(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    success = database.toggle_schedule_active(schedule_id, user_id)
    if success:
        updated_schedule = database.get_schedule_by_id(schedule_id, user_id)
        return jsonify(updated_schedule), 200
    else:
        existing = database.get_schedule_by_id(schedule_id, user_id)
        if not existing:
            return jsonify({"error": "Schedule not found"}), 404
        else:
            return jsonify({"error": "Failed to toggle schedule status"}), 500


@api_bp.route("/schedules/<int:schedule_id>/play_now", methods=["POST"])
@limiter.limit("10 per minute")
def api_play_schedule_now(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    schedule_info = database.get_schedule_by_id(schedule_id, user_id)
    if not schedule_info:
        return jsonify({"error": "Schedule not found"}), 404

    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503

    device_id = schedule_info["target_device_id"]
    playlist_uri = schedule_info["playlist_uri"]
    volume = schedule_info.get("volume")
    shuffle_enabled = bool(schedule_info.get("shuffle_state", False))

    current_app.logger.info(
        f"Manual Play Now for Schedule {schedule_id}: URI={playlist_uri}, Device={device_id}, Shuffle={shuffle_enabled}"
    )

    playback_params = {"device_id": device_id, "context_uri": playlist_uri}
    if not shuffle_enabled:
        playback_params["offset"] = {"position": 0}
        current_app.logger.info("Setting playback offset to track 0 for manual play (Shuffle is OFF).")

    success = False
    try:
        if volume is not None:
            current_app.logger.info(f"Setting volume to {volume}% for device {device_id}")
            sp.volume(volume_percent=volume, device_id=device_id)
            _time.sleep(0.5)
        current_app.logger.debug(f"Attempting sp.start_playback for manual play with params: {playback_params}")
        sp.start_playback(**playback_params)
        current_app.logger.info(f"Playback command sent for manual play (Schedule {schedule_id}).")
        success = True
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error during manual playback start for schedule {schedule_id}: {e}")
        success = False
    except Exception as e:
        current_app.logger.error(f"Unexpected error during manual playback start for schedule {schedule_id}: {e}", exc_info=True)
        success = False

    if success:
        current_app.logger.info(f"Attempting to set shuffle state to {shuffle_enabled} for manual play...")
        try:
            sleep_duration = 1.5
            _time.sleep(sleep_duration)
            sp.shuffle(state=shuffle_enabled, device_id=device_id)
            current_app.logger.info(f"Shuffle state set to {shuffle_enabled} successfully after {sleep_duration}s delay.")
            try:
                check_delay = 0.5
                _time.sleep(check_delay)
                current_state = sp.current_playback()
                if current_state and current_state.get("device") and current_state.get("device").get("id") == device_id:
                    api_shuffle_state = current_state.get("shuffle_state", "N/A")
                    current_app.logger.info(f"Checked state {check_delay:.1f}s after shuffle command:")
                    current_app.logger.info(f"  API shuffle_state reported: {api_shuffle_state} (Expected: {shuffle_enabled})")
                    if api_shuffle_state != shuffle_enabled:
                        current_app.logger.warning(
                            f"  --> Shuffle state mismatch: Command sent for {shuffle_enabled}, but API reports {api_shuffle_state}."
                        )
            except Exception as check_e:
                current_app.logger.warning(f"  Could not verify shuffle state after setting: {check_e}")
        except SpotifyException as shuffle_e:
            current_app.logger.warning(f"Could not set shuffle state to {shuffle_enabled} for manual play: {shuffle_e}")
        except Exception as general_shuffle_e:
            current_app.logger.error(f"Unexpected error setting shuffle state for manual play: {general_shuffle_e}", exc_info=True)

        return jsonify({"message": "Playback initiated"}), 200
    else:
        return jsonify({"error": "Failed to initiate playback via Spotify API"}), 502


@api_bp.route("/schedules/<int:schedule_id>/stop_now", methods=["POST"])
@limiter.limit("10 per minute")
def api_stop_schedule_now(schedule_id):
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    schedule_info = database.get_schedule_by_id(schedule_id, user_id)
    if not schedule_info:
        return jsonify({"error": "Schedule not found"}), 404

    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503

    device_id = schedule_info["target_device_id"]
    current_app.logger.info(f"Manual Stop Now for Schedule {schedule_id}: Device={device_id}")

    try:
        current_state = sp.current_playback()
        if not current_state or not current_state.get("is_playing"):
            current_app.logger.info(f"Stop Now for Schedule {schedule_id}: Nothing is currently playing.")
            return jsonify({"message": "Nothing is currently playing"}), 200

        active_device_id = current_state.get("device", {}).get("id")
        if active_device_id != device_id:
            active_device_name = current_state.get("device", {}).get("name", "Unknown")
            current_app.logger.info(
                f"Stop Now for Schedule {schedule_id}: Playback is active on different device ({active_device_name})."
            )
            return jsonify({"message": f"Playback is active on {active_device_name}, not on this schedule's device"}), 200

        sp.pause_playback()
        current_app.logger.info(f"Pause command sent for manual stop (Schedule {schedule_id}).")
        return jsonify({"message": "Playback stopped"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error during manual playback stop for schedule {schedule_id}: {e}")
        return jsonify({"error": "Failed to stop playback via Spotify API"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error during manual playback stop for schedule {schedule_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to stop playback"}), 500


@api_bp.route("/current_playback", methods=["GET"])
@limiter.limit("60 per minute")
def api_current_playback():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503

    try:
        current = sp.current_playback(additional_types="episode")
        if not current or not current.get("item"):
            return jsonify({"is_playing": False, "track": None, "next_track": None}), 200

        item = current["item"]
        track_data = {
            "name": item.get("name", "Unknown"),
            "artists": ", ".join([a["name"] for a in item.get("artists", [])]),
            "album": item.get("album", {}).get("name", ""),
            "image": item.get("album", {}).get("images", [{}])[0].get("url", ""),
            "duration_ms": item.get("duration_ms", 0),
            "progress_ms": current.get("progress_ms", 0),
        }

        up_next = []
        try:
            queue = sp.queue()
            queue_list = queue.get("queue", [])
            for next_item in queue_list[:3]:
                if next_item:
                    up_next.append({
                        "name": next_item.get("name", "Unknown"),
                        "artists": ", ".join([a["name"] for a in next_item.get("artists", [])]),
                        "album": next_item.get("album", {}).get("name", ""),
                        "image": next_item.get("album", {}).get("images", [{}])[0].get("url", ""),
                    })
        except Exception:
            pass

        return (
            jsonify(
                {
                    "is_playing": current.get("is_playing", False),
                    "device_name": current.get("device", {}).get("name", "Unknown"),
                    "track": track_data,
                    "up_next": up_next,
                }
            ),
            200,
        )
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error during current playback fetch: {e}")
        return jsonify({"error": "Failed to fetch playback state"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error during current playback fetch: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch playback state"}), 500


@api_bp.route("/play_now", methods=["POST"])
@limiter.limit("10 per minute")
def api_play_arbitrary_now():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    is_valid, error_msg = validation.validate_playback_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503

    success = spotify_client.start_playback(
        sp,
        device_id=data["device_id"],
        playlist_uri=data["playlist_uri"],
        volume=data.get("volume"),
    )

    if success:
        return jsonify({"message": "Playback initiated"}), 200
    else:
        return jsonify({"error": "Failed to initiate playback via Spotify API"}), 502


@api_bp.route("/playback/pause", methods=["POST"])
@limiter.limit("10 per minute")
def api_playback_pause():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        sp.pause_playback()
        current_app.logger.info("Playback paused via API.")
        return jsonify({"message": "Playback paused"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error pausing playback: {e}")
        return jsonify({"error": "Failed to pause playback"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error pausing playback: {e}", exc_info=True)
        return jsonify({"error": "Failed to pause playback"}), 500


@api_bp.route("/playback/play", methods=["POST"])
@limiter.limit("10 per minute")
def api_playback_play():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        sp.start_playback()
        current_app.logger.info("Playback resumed via API.")
        return jsonify({"message": "Playback resumed"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error resuming playback: {e}")
        return jsonify({"error": "Failed to resume playback"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error resuming playback: {e}", exc_info=True)
        return jsonify({"error": "Failed to resume playback"}), 500


@api_bp.route("/playback/next", methods=["POST"])
@limiter.limit("10 per minute")
def api_playback_next():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        sp.next_track()
        current_app.logger.info("Skipped to next track via API.")
        return jsonify({"message": "Skipped to next track"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error skipping track: {e}")
        return jsonify({"error": "Failed to skip track"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error skipping track: {e}", exc_info=True)
        return jsonify({"error": "Failed to skip track"}), 500


@api_bp.route("/schedules/export", methods=["GET"])
@limiter.limit("30 per minute")
def api_export_schedules():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    schedules = database.get_all_schedules(user_id)
    export_data = []
    for s in schedules:
        export_data.append({
            "playlist_uri": s["playlist_uri"],
            "playlist_name": s["playlist_name"],
            "target_device_id": s["target_device_id"],
            "target_device_name": s["target_device_name"],
            "days_of_week": s["days_of_week"],
            "start_time_local": s["start_time_local"],
            "stop_time_local": s["stop_time_local"],
            "volume": s["volume"],
            "timezone": s["timezone"],
            "shuffle_state": bool(s.get("shuffle_state", 0)),
            "is_active": bool(s.get("is_active", 1)),
        })
    return jsonify({"schedules": export_data, "exported_at": datetime.now(pytz.utc).isoformat()}), 200


@api_bp.route("/schedules/import", methods=["POST"])
@limiter.limit("10 per minute")
def api_import_schedules():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json or {}
    schedules = data.get("schedules", [])
    if not isinstance(schedules, list):
        return jsonify({"error": "schedules must be a list"}), 400

    imported_count = 0
    errors = []
    for idx, item in enumerate(schedules):
        item["user_spotify_id"] = user_id
        is_valid, error_msg = validation.validate_schedule_payload(item, partial=False)
        if not is_valid:
            errors.append({"index": idx, "error": error_msg})
            continue
        try:
            database.add_schedule(item)
            imported_count += 1
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    return jsonify({
        "imported": imported_count,
        "errors": errors,
        "total": len(schedules),
    }), 200 if not errors else 207


@api_bp.route("/test_device", methods=["POST"])
@limiter.limit("10 per minute")
def api_test_device():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json or {}
    device_id = data.get("device_id")
    playlist_uri = data.get("playlist_uri")
    if not device_id:
        return jsonify({"error": "device_id is required"}), 400
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        playback_params = {"device_id": device_id}
        if playlist_uri and playlist_uri.startswith("spotify:"):
            playback_params["context_uri"] = playlist_uri
            playback_params["offset"] = {"position": 0}
        sp.start_playback(**playback_params)
        current_app.logger.info(f"Test playback started on device {device_id}")

        def stop_test():
            try:
                sp.pause_playback(device_id=device_id)
                current_app.logger.info(f"Test playback stopped on device {device_id} after 3s")
            except Exception as e:
                current_app.logger.warning(f"Test playback auto-stop failed: {e}")

        import threading
        threading.Timer(3.0, stop_test).start()
        return jsonify({"message": "Test playback started (3 seconds)"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error during test playback: {e}")
        return jsonify({"error": "Failed to start test playback"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error during test playback: {e}", exc_info=True)
        return jsonify({"error": "Failed to start test playback"}), 500


@api_bp.route("/playback/volume", methods=["POST"])
@limiter.limit("60 per minute")
def api_playback_volume():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.json or {}
    volume = data.get("volume")
    if not isinstance(volume, int) or not (0 <= volume <= 100):
        return jsonify({"error": "volume must be integer 0-100"}), 400
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        sp.volume(volume_percent=volume)
        current_app.logger.info(f"Volume set to {volume}% via API.")
        return jsonify({"message": f"Volume set to {volume}%", "volume": volume}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error setting volume: {e}")
        return jsonify({"error": "Failed to set volume"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error setting volume: {e}", exc_info=True)
        return jsonify({"error": "Failed to set volume"}), 500


@api_bp.route("/playback/previous", methods=["POST"])
@limiter.limit("10 per minute")
def api_playback_previous():
    user_id = session.get("spotify_user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    sp = spotify_client.get_spotify_client()
    if not sp:
        return jsonify({"error": "Spotify client unavailable"}), 503
    try:
        sp.previous_track()
        current_app.logger.info("Skipped to previous track via API.")
        return jsonify({"message": "Skipped to previous track"}), 200
    except SpotifyException as e:
        current_app.logger.error(f"Spotify API error going to previous track: {e}")
        return jsonify({"error": "Failed to go to previous track"}), 502
    except Exception as e:
        current_app.logger.error(f"Unexpected error going to previous track: {e}", exc_info=True)
        return jsonify({"error": "Failed to go to previous track"}), 500


@api_bp.route("/health", methods=["GET"])
@limiter.limit("60 per minute")
def api_health():
    """Health check endpoint for monitoring."""
    db_ok = True
    try:
        conn = database.get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        current_app.logger.error(f"Health check DB failed: {e}")
        db_ok = False

    status = {"status": "healthy" if db_ok else "unhealthy", "database": "ok" if db_ok else "error"}
    code = 200 if db_ok else 503
    return jsonify(status), code
