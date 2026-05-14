#!/usr/bin/env python
# -*- coding: utf-8 -*-
# play_spotify_playlist.py - Thin CLI wrapper around shared libraries

import argparse
import os
import sys
import time

import spotipy
from dotenv import load_dotenv

import database
import services
import spotify_client

# Load environment variables
load_dotenv()


def get_spotify_client(user_id):
    """Returns a Spotipy client for CLI use by fetching the token from the database."""
    if not user_id:
        print(
            "\nError: --user-id is required. Use --list-users to see available user IDs."
        )
        sys.exit(1)

    token_info = database.get_user_token(user_id)
    if not token_info:
        print(
            f"\nError: No token found in database for user '{user_id}'.\n"
            "       Please log in via the web application first."
        )
        sys.exit(1)

    now = int(time.time())
    if token_info["expires_at"] - now < 60:
        print(f"Token for user '{user_id}' expired. Refreshing...")
        try:
            token_info = spotify_client.refresh_access_token(
                token_info["refresh_token"]
            )
            database.save_user_token(user_id, token_info)
            print("Token refreshed and saved to database.")
        except Exception as e:
            print(f"Error refreshing token for user '{user_id}': {e}")
            sys.exit(1)

    try:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        # Quick validation
        user = sp.current_user()
        print(f"Authenticated as: {user.get('display_name', user.get('id'))}")
        return sp
    except Exception as e:
        print(f"\nError creating Spotify client: {e}")
        sys.exit(1)


def _list_devices_internal(available_devices):
    """Helper to print a formatted device list."""
    if not available_devices:
        print("(None found or active)")
        return
    for i, device in enumerate(available_devices):
        active_status = " (Currently Active)" if device.get("is_active") else ""
        volume = f" - Vol: {device.get('volume_percent', 'N/A')}%"
        print(f"- Name: {device.get('name')}")
        print(f"  Type: {device.get('type')}{active_status}{volume}")
        print(f"  ID:   {device.get('id')}")
        print("-" * 10)


def list_devices(sp):
    """Lists available Spotify playback devices."""
    print("\nFetching available devices...")
    try:
        devices = spotify_client.get_user_devices(sp)
        if devices is None:
            print("Error fetching devices from Spotify API.")
            return
        if not devices:
            print("No active Spotify devices found.")
            print("Hint: Ensure Spotify is open and active on at least one device.")
            return
        print("--- Available Devices ---")
        _list_devices_internal(devices)
    except Exception as e:
        print(f"Error fetching devices: {e}")


def list_playlists(sp):
    """Lists the current user's playlists (from Spotify API directly)."""
    print("\nFetching your playlists from Spotify API...")
    try:
        all_playlists = spotify_client.get_all_user_playlists(sp)
        print(f"--- Your Playlists ({len(all_playlists)} found on Spotify) ---")
        if not all_playlists:
            print("(None found)")
            return
        for playlist in all_playlists:
            owner = playlist.get("owner", {}).get("display_name", "N/A")
            collab = " (Collaborative)" if playlist.get("collaborative") else ""
            public = " (Public)" if playlist.get("public") else " (Private)"
            print(f"- Name: {playlist.get('name')}{collab}{public}")
            print(f"  Owner: {owner}")
            print(f"  Tracks: {playlist.get('tracks', {}).get('total', 'N/A')}")
            print(f"  ID:   {playlist.get('id')}")
            print(f"  URI:  {playlist.get('uri')}")
            print("-" * 10)
    except Exception as e:
        print(f"Error fetching playlists: {e}")


def find_device(sp, device_name_query):
    """Finds an active device by name."""
    print(f"\nSearching for device containing '{device_name_query}'...")
    try:
        devices = spotify_client.get_user_devices(sp)
        if devices is None or not devices:
            print("Error: No active Spotify devices found during search.")
            return None

        found_device = None
        for device in devices:
            if device.get("name", "").lower() == device_name_query.lower():
                found_device = device
                break

        if not found_device:
            for device in devices:
                if device_name_query.lower() in device.get("name", "").lower():
                    found_device = device
                    break

        if found_device:
            print(
                f"Found device: {found_device.get('name')} (ID: {found_device.get('id')})"
            )
            return found_device.get("id")

        print(f"Error: No device found matching '{device_name_query}'.")
        print("Available devices:")
        _list_devices_internal(devices)
        return None
    except Exception as e:
        print(f"Error searching for device: {e}")
        return None


def find_playlist(sp, playlist_query):
    """Finds a playlist by name or URI/ID."""
    if playlist_query.startswith("spotify:playlist:") or len(playlist_query) == 22:
        playlist_uri = playlist_query
        if not playlist_uri.startswith("spotify:playlist:"):
            playlist_uri = f"spotify:playlist:{playlist_query}"
        print(f"\nVerifying playlist by URI/ID: {playlist_uri}")
        try:
            playlist = sp.playlist(playlist_uri, fields="name,uri,owner.display_name")
            owner_display = playlist.get("owner", {}).get(
                "display_name", "Unknown Owner"
            )
            print(
                f"Found playlist: {playlist.get('name', 'Unnamed Playlist')} (Owner: {owner_display})"
            )
            return playlist.get("uri")
        except Exception as e:
            print(f"Error accessing playlist by URI/ID: {e}")
            return None

    print(f"\nSearching for playlist matching '{playlist_query}'...")
    try:
        results = sp.search(q=playlist_query, type="playlist", limit=15)
        if not results or not results.get("playlists"):
            print(f"Error: No playlist found matching '{playlist_query}'.")
            return None

        playlists = [p for p in results["playlists"]["items"] if p]
        if not playlists:
            print(f"Error: No valid playlist data found matching '{playlist_query}'.")
            return None

        if len(playlists) == 1:
            selected = playlists[0]
            print(f"Found unique playlist: {selected.get('name')}")
            return selected.get("uri")

        print("\nMultiple playlists found. Please choose one:")
        for i, item in enumerate(playlists):
            owner_name = item.get("owner", {}).get("display_name", "Unknown Owner")
            print(
                f"{i + 1}: {item.get('name', 'Unnamed Playlist')} (Owner: {owner_name})"
            )
        while True:
            try:
                choice = int(input(f"Enter number (1-{len(playlists)}): ")) - 1
                if 0 <= choice < len(playlists):
                    print(f"Selected: {playlists[choice].get('name')}")
                    return playlists[choice].get("uri")
                print("Invalid choice number.")
            except ValueError:
                print("Please enter a number.")
    except Exception as e:
        print(f"Error searching for playlists: {e}")
        return None


# --- Main Execution ---
if __name__ == "__main__":
    print(
        "Note: For export functionality (--export-data), 'pandas' and 'openpyxl' are required."
    )
    print("You can install them using: pip install pandas openpyxl\n")

    parser = argparse.ArgumentParser(
        description="Control Spotify playback, list items, manage history/playlists, or export synced data.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--list-devices", action="store_true", help="List available playback devices."
    )
    action_group.add_argument(
        "--list-playlists",
        action="store_true",
        help="List your playlists (direct from Spotify API).",
    )
    action_group.add_argument(
        "--update-history",
        action="store_true",
        help="Fetch recent plays and add to DB.",
    )
    action_group.add_argument(
        "--recent-playlists",
        action="store_true",
        help="Show recently played playlists from DB.",
    )
    action_group.add_argument(
        "--sync-playlists",
        action="store_true",
        help="Sync all user playlists and tracks to local DB.",
    )
    action_group.add_argument(
        "--list-users",
        action="store_true",
        help="List Spotify user IDs with stored tokens in the database.",
    )

    parser.add_argument(
        "--user-id",
        type=str,
        help="Spotify user ID to act as (required for auth-dependent actions).",
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Name of the device to play on (requires --playlist).",
    )
    parser.add_argument(
        "--playlist",
        type=str,
        help="Name, ID, or URI of the playlist to play (requires --device).",
    )
    parser.add_argument(
        "--export-data",
        type=str,
        metavar="FILENAME",
        help="Export synced playlists and tracks to the specified file.\n"
        "File type (xlsx, csv, json) determined by filename extension.\n"
        "For CSV, two files: '<FILENAME>_playlists.csv' & '<FILENAME>_tracks.csv'.",
    )
    args = parser.parse_args()

    is_playback_action = bool(args.device and args.playlist)
    is_action_flag_present = any(
        [
            args.list_devices,
            args.list_playlists,
            args.update_history,
            args.recent_playlists,
            args.sync_playlists,
            args.list_users,
        ]
    )
    is_export_action = args.export_data is not None

    num_major_actions = sum(
        [is_playback_action, is_action_flag_present, is_export_action]
    )

    if num_major_actions > 1:
        parser.error(
            "Error: Please specify only one major action category:\n"
            "  1. Playback (using --device and --playlist together).\n"
            "  2. An action flag (--list-devices, --sync-playlists, etc.).\n"
            "  3. Data export (using --export-data FILENAME).\n"
            "These categories cannot be combined."
        )

    if (args.device or args.playlist) and not is_playback_action:
        parser.error(
            "Error: --device and --playlist must be used together for playback."
        )

    market_code = os.getenv("SPOTIPY_MARKET")
    if market_code:
        print(f"Using market code '{market_code}' from environment.")
    else:
        print("Market code not set (SPOTIPY_MARKET), API calls use default behavior.")

    needs_auth = is_action_flag_present or is_playback_action
    needs_db = (
        args.update_history
        or args.recent_playlists
        or args.sync_playlists
        or is_export_action
        or args.list_users
    )

    sp = None
    conn = None
    action_taken_or_attempted = False

    try:
        if needs_db:
            print(f"Connecting to database: {database.SCHEDULE_DB_FILE}")
            conn = database.get_db_connection()

        if args.list_users:
            action_taken_or_attempted = True
            users = database.list_user_ids_with_tokens()
            if users:
                print("\n--- Users with stored tokens ---")
                for uid in users:
                    print(f"- {uid}")
            else:
                print("\nNo users with stored tokens found in the database.")

        elif is_export_action:
            action_taken_or_attempted = True
            if conn:
                services.export_data_to_file(conn, args.export_data)
            else:
                print("Error: Database connection not available for export.")

        elif is_action_flag_present:
            action_taken_or_attempted = True
            if needs_auth:
                sp = get_spotify_client(args.user_id)
                if not sp:
                    sys.exit(1)
            if args.list_devices:
                list_devices(sp)
            elif args.list_playlists:
                list_playlists(sp)
            elif args.update_history:
                services.update_history_db(sp, conn)
            elif args.recent_playlists:
                services.show_recent_playlists(sp, conn, market_code)
            elif args.sync_playlists:
                services.sync_all_playlists_and_tracks(sp, conn)

        elif is_playback_action:
            action_taken_or_attempted = True
            sp = get_spotify_client(args.user_id)
            if not sp:
                sys.exit(1)
            device_id = find_device(sp, args.device)
            playlist_uri = None
            if device_id:
                playlist_uri = find_playlist(sp, args.playlist)

            if device_id and playlist_uri:
                try:
                    print(
                        f"\nAttempting to start playlist on device '{args.device}'..."
                    )
                    spotify_client.start_playback(
                        sp, device_id=device_id, playlist_uri=playlist_uri
                    )
                    print("Playback command sent successfully!")
                except Exception as e:
                    print(f"\nError starting playback: {e}")
            else:
                print("\nPlayback aborted: device or playlist not identified.")

        if num_major_actions == 0:
            print("\nNo action specified.")
            parser.print_help()
        elif num_major_actions > 0 and not action_taken_or_attempted:
            print("\nAn action was specified, but it could not be dispatched.")
            parser.print_help()

    finally:
        if conn:
            conn.close()
