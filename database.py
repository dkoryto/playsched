import sqlite3
import os
import datetime
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()
SCHEDULE_DB_FILE = os.getenv("SCHEDULE_DB_FILE", "playsched.db")

__all__ = [
    "SCHEDULE_DB_FILE",
    "get_db_connection",
    "create_tables",
    "add_schedule",
    "get_all_schedules",
    "get_schedule_by_id",
    "update_schedule",
    "delete_schedule",
    "toggle_schedule_active",
    "get_active_schedules_for_scheduler",
    "update_schedule_trigger_info",
    "save_user_token",
    "get_user_token",
    "delete_user_token",
    "list_user_ids_with_tokens",
    "acquire_scheduler_lock",
    "release_scheduler_lock",
    "renew_scheduler_lock",
]


def _get_cipher():
    """Returns a Fernet cipher instance using TOKEN_ENCRYPTION_KEY from env."""
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set. Generate one with:\n"
            "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypts a token string. Returns ciphertext string."""
    if not plaintext:
        return ""
    return _get_cipher().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypts a token string. Falls back to returning raw value if decryption fails (plaintext legacy)."""
    if not ciphertext:
        return ""
    try:
        return _get_cipher().decrypt(ciphertext.encode()).decode()
    except Exception:
        # Likely already plaintext (legacy). Return as-is so it gets re-encrypted on next save.
        return ciphertext


def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(SCHEDULE_DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return conn


def create_tables() -> None:
    """Creates the schedules table if it doesn't exist (including shuffle_state)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # shuffle_state column included in the initial table definition
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_spotify_id TEXT NOT NULL,
                playlist_uri TEXT NOT NULL,
                playlist_name TEXT,
                target_device_id TEXT NOT NULL,
                target_device_name TEXT,
                days_of_week TEXT NOT NULL,
                start_time_local TEXT NOT NULL,
                stop_time_local TEXT,
                volume INTEGER,
                is_active BOOLEAN DEFAULT 1,
                timezone TEXT NOT NULL,
                play_once_triggered BOOLEAN DEFAULT 0,
                last_triggered_utc TEXT,
                shuffle_state BOOLEAN DEFAULT 0, -- Added shuffle state (0=false, 1=true)
                sort_order INTEGER DEFAULT 0
            )
        """
        )
        # --- CLI/HISTORY tables ---
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playback_history (
                played_at TEXT PRIMARY KEY,
                track_id TEXT NOT NULL,
                track_name TEXT,
                track_uri TEXT,
                artist_names TEXT,
                album_name TEXT,
                context_type TEXT,
                context_uri TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS synced_playlists (
                id TEXT PRIMARY KEY,
                name TEXT,
                uri TEXT,
                owner_display_name TEXT,
                api_total_tracks INTEGER,
                retrieved_at TEXT NOT NULL,
                is_removed_from_spotify BOOLEAN DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS synced_playlist_tracks (
                playlist_id TEXT NOT NULL,
                track_id TEXT NOT NULL,
                track_name TEXT,
                artist_names TEXT,
                track_uri TEXT,
                position INTEGER,
                added_to_playlist_at_spotify TEXT,
                last_seen_in_api_sync_at TEXT NOT NULL,
                is_removed_from_playlist BOOLEAN DEFAULT 0,
                PRIMARY KEY (playlist_id, track_id),
                FOREIGN KEY (playlist_id) REFERENCES synced_playlists(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synced_playlist_tracks_playlist_id "
            "ON synced_playlist_tracks (playlist_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synced_playlists_is_removed "
            "ON synced_playlists (is_removed_from_spotify)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_synced_playlist_tracks_removed "
            "ON synced_playlist_tracks (is_removed_from_playlist)"
        )
        # --- end CLI/HISTORY tables ---

        # --- User token cache table (replaces .spotify_token_cache.json) ---
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_spotify_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                token_type TEXT,
                scope TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        # --- end token cache table ---

        # --- Scheduler distributed lock table ---
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_lock (
                lock_name TEXT PRIMARY KEY,
                acquired_by TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        # --- end scheduler lock table ---

        conn.commit()
        print("Database tables checked/created.")
    except sqlite3.Error as e:
        print(f"Database error during table creation: {e}")
        # raise # Decide if you want to stop the app
    finally:
        conn.close()


# --- CRUD Functions for Schedules ---


def add_schedule(data: dict) -> int | None:
    # Add shuffle_state to INSERT
    sql = (
        "INSERT INTO schedules(user_spotify_id, playlist_uri, playlist_name, "
        "target_device_id, target_device_name, days_of_week, start_time_local, "
        "stop_time_local, volume, is_active, timezone, play_once_triggered, "
        "last_triggered_utc, shuffle_state, sort_order) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (
                data["user_spotify_id"],
                data["playlist_uri"],
                data.get("playlist_name", ""),
                data["target_device_id"],
                data.get("target_device_name", ""),
                data["days_of_week"],
                data["start_time_local"],
                data.get("stop_time_local"),
                data.get("volume"),
                data.get("is_active", 1),
                data["timezone"],
                data.get("play_once_triggered", 0),
                None,
                data.get("shuffle_state", 0),
                data.get("sort_order", 0),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding schedule: {e}")
        return None
    finally:
        conn.close()


def get_all_schedules(user_spotify_id: str) -> list[dict]:
    """Retrieves all schedules for a given user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM schedules WHERE user_spotify_id = ? ORDER BY sort_order ASC, id ASC",
            (user_spotify_id,)
        )
        schedules = [dict(row) for row in cursor.fetchall()]
        return schedules
    except sqlite3.Error as e:
        print(f"Database error getting all schedules: {e}")
        return []
    finally:
        conn.close()


def get_schedule_by_id(schedule_id: int, user_spotify_id: str) -> dict | None:
    """Retrieves a specific schedule by ID for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM schedules WHERE id = ? AND user_spotify_id = ?",
            (schedule_id, user_spotify_id),
        )
        schedule = cursor.fetchone()
        return dict(schedule) if schedule else None
    except sqlite3.Error as e:
        print(f"Database error getting schedule by ID: {e}")
        return None
    finally:
        conn.close()


def update_schedule(schedule_id: int, user_spotify_id: str, data: dict) -> bool:
    fields = []
    values = []
    # Add shuffle_state to allowed fields
    allowed_fields = [
        "playlist_uri",
        "playlist_name",
        "target_device_id",
        "target_device_name",
        "days_of_week",
        "start_time_local",
        "stop_time_local",
        "volume",
        "is_active",
        "timezone",
        "shuffle_state",
        "sort_order",
    ]
    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = ?")
            # Convert boolean for shuffle_state if necessary
            value = data[field]
            if field == "shuffle_state":
                value = 1 if value else 0  # Ensure it's stored as 0 or 1
            values.append(value)

    if not fields:
        return False  # Nothing to update

    sql = (
        f"UPDATE schedules SET {', '.join(fields)} WHERE id = ? AND user_spotify_id = ?"
    )
    values.extend([schedule_id, user_spotify_id])

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0  # Return True if update happened
    except sqlite3.Error as e:
        print(f"Database error updating schedule {schedule_id}: {e}")
        return False
    finally:
        conn.close()


def delete_schedule(schedule_id: int, user_spotify_id: str) -> bool:
    """Deletes a schedule."""
    sql = "DELETE FROM schedules WHERE id = ? AND user_spotify_id = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (schedule_id, user_spotify_id))
        conn.commit()
        return cursor.rowcount > 0  # Return True if deletion happened
    except sqlite3.Error as e:
        print(f"Database error deleting schedule {schedule_id}: {e}")
        return False
    finally:
        conn.close()


def toggle_schedule_active(schedule_id: int, user_spotify_id: str) -> bool:
    """Toggles the is_active status of a schedule."""
    # First get current status
    current_schedule = get_schedule_by_id(schedule_id, user_spotify_id)
    if not current_schedule:
        return False

    new_status = 1 - current_schedule["is_active"]  # Toggle 0 to 1 or 1 to 0
    sql = "UPDATE schedules SET is_active = ? WHERE id = ? AND user_spotify_id = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (new_status, schedule_id, user_spotify_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error toggling schedule {schedule_id}: {e}")
        return False
    finally:
        conn.close()


def get_active_schedules_for_scheduler() -> list[dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Add shuffle_state to SELECT list
        cursor.execute(
            "SELECT id, user_spotify_id, playlist_uri, target_device_id, "
            "days_of_week, start_time_local, stop_time_local, volume, timezone, "
            "play_once_triggered, last_triggered_utc, shuffle_state "
            "FROM schedules WHERE is_active = 1"
        )
        schedules = [dict(row) for row in cursor.fetchall()]
        return schedules
    except sqlite3.Error as e:
        print(f"Database error getting active schedules for scheduler: {e}")
        return []
    finally:
        conn.close()


def swap_sort_order(schedule_id_a: int, schedule_id_b: int, user_spotify_id: str) -> bool:
    """Swaps sort_order between two schedules."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, sort_order FROM schedules WHERE id IN (?, ?) AND user_spotify_id = ?",
            (schedule_id_a, schedule_id_b, user_spotify_id)
        )
        rows = cursor.fetchall()
        if len(rows) != 2:
            return False
        order_a = dict(rows[0])["sort_order"]
        order_b = dict(rows[1])["sort_order"]
        cursor.execute(
            "UPDATE schedules SET sort_order = ? WHERE id = ?",
            (order_b, schedule_id_a)
        )
        cursor.execute(
            "UPDATE schedules SET sort_order = ? WHERE id = ?",
            (order_a, schedule_id_b)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error swapping sort order: {e}")
        return False
    finally:
        conn.close()


def update_schedule_trigger_info(schedule_id: int, trigger_time_utc_iso: str, played_once: bool = False) -> None:
    """Updates trigger info after a schedule runs."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if played_once:
            cursor.execute(
                "UPDATE schedules SET last_triggered_utc = ?, play_once_triggered = 1 WHERE id = ?",
                (trigger_time_utc_iso, schedule_id),
            )
        else:
            cursor.execute(
                "UPDATE schedules SET last_triggered_utc = ? WHERE id = ?",
                (trigger_time_utc_iso, schedule_id),
            )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error updating trigger info for schedule {schedule_id}: {e}")
    finally:
        conn.close()


# --- Token CRUD ---


def save_user_token(user_id: str, token_info: dict) -> bool:
    """Upserts Spotify token info for a user. Encrypts refresh_token at rest."""
    sql = (
        "INSERT INTO user_tokens (user_spotify_id, access_token, refresh_token, "
        "expires_at, token_type, scope, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(user_spotify_id) DO UPDATE SET "
        "access_token=excluded.access_token, refresh_token=excluded.refresh_token, "
        "expires_at=excluded.expires_at, token_type=excluded.token_type, "
        "scope=excluded.scope, updated_at=excluded.updated_at"
    )
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (
                user_id,
                token_info.get("access_token"),
                encrypt_token(token_info.get("refresh_token")),
                token_info.get("expires_at"),
                token_info.get("token_type"),
                token_info.get("scope"),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error saving token for user {user_id}: {e}")
        return False
    finally:
        conn.close()


def get_user_token(user_id: str) -> dict | None:
    """Retrieves token info dict for a user, or None. Decrypts refresh_token."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_token, refresh_token, expires_at, token_type, scope "
            "FROM user_tokens WHERE user_spotify_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "access_token": row["access_token"],
            "refresh_token": decrypt_token(row["refresh_token"]),
            "expires_at": row["expires_at"],
            "token_type": row["token_type"],
            "scope": row["scope"],
        }
    except sqlite3.Error as e:
        print(f"Database error getting token for user {user_id}: {e}")
        return None
    finally:
        conn.close()


def delete_user_token(user_id: str) -> bool:
    """Deletes a user's token record."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_tokens WHERE user_spotify_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error deleting token for user {user_id}: {e}")
        return False
    finally:
        conn.close()


def list_user_ids_with_tokens() -> list[str]:
    """Returns a list of user_spotify_id strings that have stored tokens."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_spotify_id FROM user_tokens ORDER BY updated_at DESC"
        )
        return [row["user_spotify_id"] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error listing users with tokens: {e}")
        return []
    finally:
        conn.close()


# --- Scheduler Lock Functions ---


SCHEDULER_LOCK_NAME = "scheduler_main"
DEFAULT_LOCK_TTL_SECONDS = 300


def acquire_scheduler_lock(instance_id: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> bool:
    """Attempts to acquire the scheduler lock. Returns True if acquired or already held by this instance."""
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(seconds=ttl_seconds)
    conn = get_db_connection()
    try:
        # Use immediate transaction to reduce race-conditions between connections
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT acquired_by, expires_at FROM scheduler_lock WHERE lock_name = ?",
            (SCHEDULER_LOCK_NAME,),
        )
        row = cursor.fetchone()
        if row:
            expires_existing = datetime.datetime.fromisoformat(row["expires_at"])
            if expires_existing > now and row["acquired_by"] != instance_id:
                conn.rollback()
                return False
            # Expired or same instance — update
            cursor.execute(
                "UPDATE scheduler_lock SET acquired_by = ?, acquired_at = ?, expires_at = ? WHERE lock_name = ?",
                (instance_id, now.isoformat(), expires.isoformat(), SCHEDULER_LOCK_NAME),
            )
        else:
            try:
                cursor.execute(
                    "INSERT INTO scheduler_lock (lock_name, acquired_by, acquired_at, expires_at) VALUES (?, ?, ?, ?)",
                    (SCHEDULER_LOCK_NAME, instance_id, now.isoformat(), expires.isoformat()),
                )
            except sqlite3.IntegrityError:
                # Another connection inserted between our SELECT and INSERT
                conn.rollback()
                return False
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error acquiring scheduler lock: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        conn.close()


def release_scheduler_lock(instance_id: str) -> bool:
    """Releases the scheduler lock if held by the given instance."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM scheduler_lock WHERE lock_name = ? AND acquired_by = ?",
            (SCHEDULER_LOCK_NAME, instance_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error releasing scheduler lock: {e}")
        return False
    finally:
        conn.close()


def renew_scheduler_lock(instance_id: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> bool:
    """Renews the lock TTL while the job is running."""
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(seconds=ttl_seconds)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scheduler_lock SET expires_at = ? WHERE lock_name = ? AND acquired_by = ?",
            (expires.isoformat(), SCHEDULER_LOCK_NAME, instance_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error renewing scheduler lock: {e}")
        return False
    finally:
        conn.close()


# Ensure tables exist when module is loaded
create_tables()
