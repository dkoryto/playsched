# PlaySched Version History

## 0.2.0 - 14 May 2026 - UI/UX Overhaul & New Features

* **Immediate Stop Playback:** Added "⏹ Stop Now" button to each schedule in the Scheduled Playlists tab, allowing instant pause of playback on the schedule's target device. Endpoint: `POST /api/schedules/<id>/stop_now`.
* **Dark Mode:** Implemented full dark/light theme toggle with system preference detection. Theme preference is persisted in `localStorage`. Includes rich dark palette with subtle gradients and glow effects.
* **Live Clock:** Added real-time date and time display in the header, with ticking seconds, using tabular numerals for stable layout.
* **Modern UI/UX Redesign:** Complete visual overhaul following 2024-2025 trends:
  * Card-based layouts with large border-radius and soft shadows
  * Glassmorphism header with `backdrop-filter: blur`
  * Responsive CSS Grid for playlists
  * Staggered fade-in animations for schedule cards
  * Pulsing status indicators with animated dots
  * Modern gradient buttons with hover lift effects
  * Improved tab design with rounded pill-style buttons
  * Enhanced form styling with focus rings and better spacing
  * Custom scrollbars and mobile-first responsive improvements
* **Project Setup:** Added `.env` configuration, auto-generated SSL certificates (`localhost.crt/key`), and dependency installation support.
* **Now Playing Widget:** Dynamic widget showing the currently playing track (title, artist, album cover, progress bar with time), active device name, and the next track in queue. Updates every 5 seconds via `GET /api/current_playback`.
* **Redesigned Live Clock:** Moved to the right side of the header, aligned with the app title. Larger, bolder monospace font for better readability.
* **Code Quality & Security Audit:**
  * Full Python codebase reformatted with `black` (PEP 8 compliant).
  * All `flake8` warnings resolved (unused imports/variables, f-string misuse, line lengths).
  * Fixed XSS vulnerabilities in frontend (`playlistSearchInput.value` in `innerHTML`, unescaped quotes in `data-name` attributes).
  * Removed leftover debug `console.log` calls from `renderSchedules()` loop.
  * Removed all emoji from schedule action buttons to prevent event-delegation edge cases.

## 0.1.1 - 2 Jun 2025 - Enhanced CLI Functionality

* **Playlist & Track Sync:** Added `--sync-playlists` command to `play_spotify_playlist.py` to fetch all user playlists (created and followed) and their tracks, storing them in new local database tables (`synced_playlists`, `synced_playlist_tracks`). Includes logic to mark items as "removed" if no longer found on Spotify, without deleting records.
* **Data Export:** Introduced `--export-data FILENAME` command to `play_spotify_playlist.py` allowing export of synced playlist and track data to Excel (`.xlsx`), CSV (two files), or JSON (`.json`) formats. Requires `pandas` and `openpyxl`.
* **Documentation:** Updated `README.md` to reflect new commands and added clarification on Spotify Developer App setup regarding the "Website" URL. Updated `requirements.txt` to include `pandas` and `openpyxl`. Updated `ROADMAP.md` to split spotify + non-spotify related features.

## 0.1.0 - 18 Apr 2025 - Initial Release

Initial release with basic functionality, including command line tool and web server connecting to database to store schedule, linking to Spotify API, find and selecting playlists for scheduling, and scheduling and editing / tracking playlists.