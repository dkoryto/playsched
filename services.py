# services.py - Shared Spotify sync, history, and export services
# Used by both CLI (play_spotify_playlist.py) and potentially the web app.

import sqlite3
import datetime
import pytz
import os


def update_history_db(sp, conn):
    """Fetches recent playback history from Spotify and stores new entries in the DB."""
    print("\nFetching recent playback history from Spotify...")
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0
    try:
        results = sp.current_user_recently_played(limit=50)
        if not results or not results.get("items"):
            print(
                "Could not retrieve recent playback history (or no history available)."
            )
            return

        print(f"Retrieved {len(results['items'])} recent tracks. Processing...")

        for item in results["items"]:
            played_at = item.get("played_at")
            track = item.get("track")
            context = item.get("context")

            if not played_at or not track:
                continue

            track_id = track.get("id")
            track_name = track.get("name")
            track_uri = track.get("uri")
            album_name = track["album"]["name"] if track.get("album") else None
            artist_names = ", ".join(
                [a["name"] for a in track.get("artists", []) if a.get("name")]
            )
            context_type = context.get("type") if context else None
            context_uri = context.get("uri") if context else None

            sql = """
                INSERT OR IGNORE INTO playback_history
                (played_at, track_id, track_name, track_uri, artist_names, album_name, context_type, context_uri)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            try:
                cursor.execute(
                    sql,
                    (
                        played_at,
                        track_id,
                        track_name,
                        track_uri,
                        artist_names,
                        album_name,
                        context_type,
                        context_uri,
                    ),
                )
                if cursor.rowcount > 0:
                    added_count += 1
                else:
                    skipped_count += 1
            except sqlite3.Error as e:
                print(
                    f"Database error inserting row for track '{track_name}' at {played_at}: {e}"
                )

        conn.commit()
        print(
            f"History update complete. Added: {added_count} new entries. "
            f"Skipped (already present): {skipped_count} entries."
        )
        print(
            "Note: Spotify API only provides the most recent ~50 played tracks per request."
        )

    except Exception as e:
        print(f"An unexpected error occurred during history update: {e}")


def show_recent_playlists(sp, conn, market_code=None, timezone_str="Europe/Paris"):
    """Queries the DB for recently played playlists and displays them."""
    print("\nQuerying database for recently played playlists...")
    cursor = conn.cursor()
    playlist_cache = {}
    try:
        sql = """
            SELECT context_uri, MAX(played_at) as last_played
            FROM playback_history
            WHERE context_type = 'playlist' AND context_uri IS NOT NULL
            GROUP BY context_uri ORDER BY last_played DESC LIMIT 50
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        if not results:
            print("No playlist history found in the database.")
            print("Hint: Run the script with --update-history first.")
            return

        print("\n--- Recently Played Playlists (from stored history) ---")
        local_tz = pytz.timezone(timezone_str)
        print(f"(Displaying times in {local_tz.zone} timezone)")

        for row in results:
            playlist_uri = row[0]
            last_played_utc_str = row[1]
            playlist_name = "Unknown Playlist"

            if playlist_uri in playlist_cache:
                playlist_name = playlist_cache[playlist_uri]
            else:
                try:
                    api_params = {"fields": "name"}
                    if market_code:
                        api_params["market"] = market_code
                    playlist_info = sp.playlist(playlist_uri, **api_params)
                    if playlist_info and playlist_info.get("name"):
                        playlist_name = playlist_info["name"]
                        playlist_cache[playlist_uri] = playlist_name
                except Exception as e:
                    print(f"  Warning: Could not fetch name for {playlist_uri}: {e}")
                    playlist_name = f"Playlist (URI: {playlist_uri})"

            try:
                if last_played_utc_str.endswith("Z"):
                    ts_part = last_played_utc_str[:-1]
                else:
                    ts_part = last_played_utc_str
                if "." in ts_part:
                    base, micro = ts_part.split(".")
                    ts_part = f"{base}.{micro:<06}"
                dt_utc = datetime.datetime.fromisoformat(ts_part).replace(
                    tzinfo=pytz.utc
                )
                dt_local = dt_utc.astimezone(local_tz)
                local_time_str = dt_local.strftime("%d/%m/%Y %H:%M:%S")
                print(f"- Name: {playlist_name}")
                print(f"  Last Played ({local_tz.zone} Time): {local_time_str}")
                print("-" * 10)
            except Exception as e:
                print(
                    f"  Error formatting time for {playlist_uri} ({last_played_utc_str}): {e}"
                )
                print(f"- Name: {playlist_name}")
                print(f"  Last Played (UTC): {last_played_utc_str}")
                print("-" * 10)
    except sqlite3.Error as e:
        print(f"Database error querying recent playlists: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in show_recent_playlists: {e}")


def sync_all_playlists_and_tracks(sp, conn):
    """
    Fetches all user's playlists and their tracks from Spotify,
    and upserts them into the local database. Marks items as 'removed'
    if they are no longer found on Spotify, instead of deleting them.
    """
    print("\n--- Starting Full Playlist and Track Sync ---")
    cursor = conn.cursor()
    now_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    now_utc_iso = now_utc.isoformat()

    cursor.execute("SELECT id FROM synced_playlists WHERE is_removed_from_spotify = 0")
    db_playlist_ids_active_before_sync = {row[0] for row in cursor.fetchall()}
    print(
        f"Found {len(db_playlist_ids_active_before_sync)} active playlists in DB before sync."
    )

    print("Fetching all user playlists from Spotify...")
    spotify_playlists_api_items = []
    offset = 0
    limit = 50
    while True:
        try:
            results = sp.current_user_playlists(limit=limit, offset=offset)
            if not results or not results.get("items"):
                break
            spotify_playlists_api_items.extend(results["items"])
            if results["next"]:
                offset += limit
            else:
                break
        except Exception as e:
            print(f"Spotify API error fetching user playlists: {e}. Aborting sync.")
            return
    print(f"Retrieved {len(spotify_playlists_api_items)} playlists from Spotify API.")

    api_playlist_ids_this_sync = set()
    playlists_processed_count = 0

    for sp_playlist_item in spotify_playlists_api_items:
        if not sp_playlist_item or not sp_playlist_item.get("id"):
            continue

        playlist_id = sp_playlist_item["id"]
        api_playlist_ids_this_sync.add(playlist_id)
        playlist_name = sp_playlist_item.get("name", "Unnamed Playlist")
        playlist_uri = sp_playlist_item.get("uri")
        owner_name = sp_playlist_item.get("owner", {}).get("display_name", "N/A")
        api_total_tracks = sp_playlist_item.get("tracks", {}).get("total", 0)

        print(f"\nProcessing playlist: '{playlist_name}' (ID: {playlist_id})")

        try:
            cursor.execute(
                """
                INSERT INTO synced_playlists (id, name, uri, owner_display_name, api_total_tracks, retrieved_at, is_removed_from_spotify)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    uri = excluded.uri,
                    owner_display_name = excluded.owner_display_name,
                    api_total_tracks = excluded.api_total_tracks,
                    retrieved_at = excluded.retrieved_at,
                    is_removed_from_spotify = 0
            """,
                (
                    playlist_id,
                    playlist_name,
                    playlist_uri,
                    owner_name,
                    api_total_tracks,
                    now_utc_iso,
                ),
            )
        except sqlite3.Error as e:
            print(f"  DB error upserting playlist '{playlist_name}': {e}")
            continue

        try:
            cursor.execute(
                "UPDATE synced_playlist_tracks SET is_removed_from_playlist = 1 WHERE playlist_id = ?",
                (playlist_id,),
            )
        except sqlite3.Error as e:
            print(f"  DB error marking old tracks for playlist '{playlist_name}': {e}")
            continue

        print(f"  Fetching tracks for playlist '{playlist_name}'...")
        spotify_playlist_track_items = []
        track_offset = 0
        track_limit = 100
        current_position_in_playlist = 0
        while True:
            try:
                fields_param = "items(added_at,track(id,name,uri,artists(name))),next"
                track_results = sp.playlist_items(
                    playlist_id,
                    limit=track_limit,
                    offset=track_offset,
                    fields=fields_param,
                )

                if not track_results or not track_results.get("items"):
                    break

                for item in track_results["items"]:
                    if item and item.get("track") and item["track"].get("id"):
                        item["current_position_in_playlist"] = (
                            current_position_in_playlist
                        )
                        spotify_playlist_track_items.append(item)
                        current_position_in_playlist += 1
                if track_results["next"]:
                    track_offset += track_limit
                else:
                    break
            except Exception as e:
                print(
                    f"  Error fetching tracks for playlist '{playlist_name}': {e}. "
                    "Skipping tracks for this playlist."
                )
                spotify_playlist_track_items = []
                break
        print(
            f"  Retrieved {len(spotify_playlist_track_items)} valid tracks from Spotify API "
            f"for playlist '{playlist_name}'."
        )

        tracks_synced_count_for_this_playlist = 0
        for item_data in spotify_playlist_track_items:
            track_info = item_data["track"]
            track_id = track_info["id"]
            track_name = track_info.get("name", "N/A")
            track_uri = track_info.get("uri")
            artist_names = ", ".join(
                [a["name"] for a in track_info.get("artists", []) if a.get("name")]
            )
            added_at_spotify_ts = item_data.get("added_at")
            position = item_data["current_position_in_playlist"]

            try:
                cursor.execute(
                    """
                    INSERT INTO synced_playlist_tracks (
                        playlist_id, track_id, track_name, artist_names, track_uri,
                        position, added_to_playlist_at_spotify, last_seen_in_api_sync_at, is_removed_from_playlist
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT(playlist_id, track_id) DO UPDATE SET
                        track_name = excluded.track_name,
                        artist_names = excluded.artist_names,
                        track_uri = excluded.track_uri,
                        position = excluded.position,
                        added_to_playlist_at_spotify = excluded.added_to_playlist_at_spotify,
                        last_seen_in_api_sync_at = excluded.last_seen_in_api_sync_at,
                        is_removed_from_playlist = 0
                """,
                    (
                        playlist_id,
                        track_id,
                        track_name,
                        artist_names,
                        track_uri,
                        position,
                        added_at_spotify_ts,
                        now_utc_iso,
                    ),
                )
                tracks_synced_count_for_this_playlist += 1
            except sqlite3.Error as e:
                print(
                    f"  DB error upserting track ID {track_id} for playlist '{playlist_name}': {e}"
                )
        print(
            f"  Upserted {tracks_synced_count_for_this_playlist} tracks for playlist '{playlist_name}' into DB."
        )
        playlists_processed_count += 1

    print(f"\nProcessed {playlists_processed_count} playlists from Spotify API.")

    removed_playlist_count = 0
    playlists_to_mark_as_globally_removed = (
        db_playlist_ids_active_before_sync - api_playlist_ids_this_sync
    )

    if playlists_to_mark_as_globally_removed:
        print(
            f"\nFound {len(playlists_to_mark_as_globally_removed)} playlists in DB that are no longer in Spotify. "
            "Marking them as removed..."
        )
        for removed_playlist_id in playlists_to_mark_as_globally_removed:
            try:
                cursor.execute(
                    "UPDATE synced_playlists SET is_removed_from_spotify = 1, retrieved_at = ? WHERE id = ?",
                    (now_utc_iso, removed_playlist_id),
                )
                cursor.execute(
                    "UPDATE synced_playlist_tracks SET is_removed_from_playlist = 1, last_seen_in_api_sync_at = ? "
                    "WHERE playlist_id = ?",
                    (now_utc_iso, removed_playlist_id),
                )
                removed_playlist_count += 1
                print(
                    f"  Marked playlist ID {removed_playlist_id} and its tracks as removed."
                )
            except sqlite3.Error as e:
                print(
                    f"  DB error marking playlist ID {removed_playlist_id} as removed: {e}"
                )
        print(
            f"Marked {removed_playlist_count} playlists (and their tracks) as removed because they are no longer on Spotify."
        )

    try:
        conn.commit()
        print("\n--- Full Playlist and Track Sync COMPLETED ---")
    except sqlite3.Error as e:
        print(f"Database commit error at the end of sync: {e}")
        print("WARNING: Some changes might not have been saved.")


def export_data_to_file(conn, filename):
    """Exports synced playlists and tracks from the database to the specified file."""
    print(f"\nAttempting to export data to '{filename}'...")

    try:
        pd_module = __import__("pandas")
    except ImportError:
        print("\nError: The 'pandas' library is required for the export functionality.")
        print("Please install it by running: pip install pandas")
        if filename.lower().endswith(".xlsx"):
            print("For Excel export, 'openpyxl' is also required: pip install openpyxl")
        return

    base_filename, extension = os.path.splitext(filename)
    extension = extension.lower()

    try:
        playlists_df = pd_module.read_sql_query("SELECT * FROM synced_playlists", conn)
        tracks_df = pd_module.read_sql_query(
            "SELECT * FROM synced_playlist_tracks", conn
        )

        if "is_removed_from_spotify" in playlists_df.columns:
            playlists_df["is_removed_from_spotify"] = playlists_df[
                "is_removed_from_spotify"
            ].astype(bool)
        if "is_removed_from_playlist" in tracks_df.columns:
            tracks_df["is_removed_from_playlist"] = tracks_df[
                "is_removed_from_playlist"
            ].astype(bool)

        if extension == ".xlsx":
            try:
                __import__("openpyxl")
            except ImportError:
                print(
                    "\nError: The 'openpyxl' library is required for Excel (.xlsx) export."
                )
                print("Please install it by running: pip install openpyxl")
                return
            with pd_module.ExcelWriter(filename, engine="openpyxl") as writer:
                playlists_df.to_excel(writer, sheet_name="Playlists", index=False)
                tracks_df.to_excel(writer, sheet_name="Tracks", index=False)
            print(f"Data successfully exported to Excel file: {filename}")
        elif extension == ".csv":
            playlist_csv_filename = f"{base_filename}_playlists.csv"
            track_csv_filename = f"{base_filename}_tracks.csv"
            playlists_df.to_csv(playlist_csv_filename, index=False, encoding="utf-8")
            tracks_df.to_csv(track_csv_filename, index=False, encoding="utf-8")
            print(
                f"Data successfully exported to CSV files: {playlist_csv_filename} and {track_csv_filename}"
            )
        elif extension == ".json":
            import json

            data_to_export = {
                "playlists": playlists_df.to_dict(orient="records"),
                "tracks": tracks_df.to_dict(orient="records"),
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data_to_export, f, ensure_ascii=False, indent=4)
            print(f"Data successfully exported to JSON file: {filename}")
        else:
            print(
                f"Error: Unsupported file extension '{extension}'. Please use .xlsx, .csv, or .json."
            )
            return

    except Exception as e:
        print(f"An unexpected error occurred during export: {e}")
