"""Translation dictionary for PlaySched UI.

ADDING A NEW LANGUAGE
=====================
1. Add a new top-level key to TRANSLATIONS (e.g. "de" for German).
2. Copy the "en" block as a template and translate every value.
3. Add the new language code to AVAILABLE_LANGUAGES (or it will be auto-detected).
4. Restart the app — no code changes in HTML/JS/Python are required.

The fallback chain works like this:
  requested_lang → fallback_lang (configurable per language) → "en" → raw key
"""

from config import Config

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "en": "English",
    "pl": "Polski",
}

# Which language to use when a key is missing in the requested language.
# If the fallback is also missing, we fall back to "en", then the raw key.
FALLBACK_MAP = {
    "pl": "en",
    # Example: "de": "en",
}

# ---------------------------------------------------------------------------
# Translation strings
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "en": {
        "title": "PlaySched - Spotify Playlist Scheduler",
        "login_prompt": "Please log in with Spotify to use the scheduler.",
        "login_button": "Login with Spotify",
        "welcome": "Welcome, {name}!",
        "logout": "Logout",
        "my_playlists": "My Playlists",
        "scheduled_playlists": "Scheduled Playlists",
        "refresh_playlists": "Refresh Playlists",
        "playlist_filter_placeholder": "Filter playlists by name...",
        "refresh_schedules": "Refresh Schedules",
        "add_schedule": "Add Schedule",
        "edit_schedule": "Edit Schedule",
        "add_schedule_from_duplicate": "Add Schedule (from Duplicate)",
        "save_schedule": "Save Schedule",
        "cancel": "Cancel",
        "play_now": "Play Now",
        "device": "Device",
        "days_of_week": "Days of Week (Leave blank to play once only):",
        "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
        "fri": "Fri", "sat": "Sat", "sun": "Sun",
        "all": "All",
        "none_play_once": "None (Play Once)",
        "start_time": "Start Time (HH:MM):",
        "stop_time": "Stop Time (HH:MM, Optional):",
        "volume": "Volume (0-100, Optional):",
        "timezone": "Timezone:",
        "shuffle": "Play in Shuffle Mode",
        "now_playing": "Now Playing",
        "up_next": "Up Next",
        "loading_playlists": "Loading playlists...",
        "loading_schedules": "Loading schedules...",
        "no_schedules": "No schedules created yet.",
        "no_playlists": "No playlists found.",
        "no_playlists_matching": 'No playlists found matching "{term}".',
        "next_run": "Next Run",
        "status": "Status",
        "active": "Active",
        "paused": "Paused",
        "played_once": "Played Once",
        "play_once": "Play Once",
        "time": "Time",
        "days": "Days",
        "vol": "Vol",
        "shuffle_short": "Shuffle",
        "on": "On",
        "off": "Off",
        "error_session_expired": "Your session may have expired. Please log in again.",
        "error_network": "A network error occurred. Please check your connection or try again later.",
        "confirm_delete_schedule": "Are you sure you want to delete this schedule?",
        "confirm_no_days": "No days selected. Schedule will play once when conditions match next, then stop. Continue?",
        "toast_playback_initiated": "Playback initiated",
        "toast_playback_stopped": "Playback stopped",
        "toast_playback_paused": "Playback paused",
        "toast_playback_resumed": "Playback resumed",
        "toast_next_track": "Skipped to next track",
        "toast_prev_track": "Skipped to previous track",
        "nothing_playing": "Nothing is currently playing",
        "playback_on_other_device": "Playback is active on {device}, not on this schedule's device",
        "select_device": "-- Select Device --",
        "no_active_devices": "No active devices found",
        "previous": "Previous",
        "pause": "Pause",
        "play": "Play",
        "stop": "Stop",
        "next": "Next",
        "schedule": "Schedule",
        "playing": "Playing...",
        "stopping": "Stopping...",
        "duplicate": "Duplicate",
        "delete": "Delete",
        "edit": "Edit",
        "toggle_pause": "Pause",
        "toggle_unpause": "Unpause",
        "loading": "Loading...",
        "failed_to_load": "Failed to load",
        "panel_password_prompt": "Enter the panel password to continue.",
        "panel_password_placeholder": "Password",
        "panel_login_button": "Unlock Panel",
        "panel_login_error": "Invalid password. Please try again.",
        "panel_logout": "Lock Panel",
        "export_schedules": "Export JSON",
        "import_schedules": "Import JSON",
        "test_device": "Test Device",
        "toast_exported": "Schedules exported",
        "toast_imported": "Schedules imported",
    },
    "pl": {
        "title": "PlaySched - Planista Playlist Spotify",
        "login_prompt": "Zaloguj się przez Spotify, aby używać planisty.",
        "login_button": "Zaloguj przez Spotify",
        "welcome": "Witaj, {name}!",
        "logout": "Wyloguj",
        "my_playlists": "Moje Playlisty",
        "scheduled_playlists": "Zaplanowane Playlisty",
        "refresh_playlists": "Odśwież Playlisty",
        "playlist_filter_placeholder": "Filtruj playlisty po nazwie...",
        "refresh_schedules": "Odśwież Harmonogramy",
        "add_schedule": "Dodaj Harmonogram",
        "edit_schedule": "Edytuj Harmonogram",
        "add_schedule_from_duplicate": "Dodaj Harmonogram (z duplikatu)",
        "save_schedule": "Zapisz Harmonogram",
        "cancel": "Anuluj",
        "play_now": "Odtwórz Teraz",
        "device": "Urządzenie",
        "days_of_week": "Dni tygodnia (zostaw puste dla jednorazowego odtworzenia):",
        "mon": "Pon", "tue": "Wt", "wed": "Śr", "thu": "Czw",
        "fri": "Pt", "sat": "Sob", "sun": "Ndz",
        "all": "Wszystkie",
        "none_play_once": "Brak (Odtwórz raz)",
        "start_time": "Godzina startu (GG:MM):",
        "stop_time": "Godzina stopu (GG:MM, opcjonalnie):",
        "volume": "Głośność (0-100, opcjonalnie):",
        "timezone": "Strefa czasowa:",
        "shuffle": "Odtwarzaj losowo",
        "now_playing": "Teraz gra",
        "up_next": "Następna",
        "loading_playlists": "Ładowanie playlist...",
        "loading_schedules": "Ładowanie harmonogramów...",
        "no_schedules": "Brak utworzonych harmonogramów.",
        "no_playlists": "Nie znaleziono playlist.",
        "no_playlists_matching": 'Nie znaleziono playlist pasujących do "{term}".',
        "next_run": "Następne uruchomienie",
        "status": "Status",
        "active": "Aktywny",
        "paused": "Wstrzymany",
        "played_once": "Odtworzono raz",
        "play_once": "Odtwórz raz",
        "time": "Godzina",
        "days": "Dni",
        "vol": "Głośność",
        "shuffle_short": "Losowo",
        "on": "Tak",
        "off": "Nie",
        "error_session_expired": "Twoja sesja mogła wygasnąć. Zaloguj się ponownie.",
        "error_network": "Wystąpił błąd sieci. Sprawdź połączenie i spróbuj ponownie.",
        "confirm_delete_schedule": "Czy na pewno chcesz usunąć ten harmonogram?",
        "confirm_no_days": "Nie wybrano dni. Harmonogram odtworzy się raz przy najbliższej okazji, a potem się zatrzyma. Kontynuować?",
        "toast_playback_initiated": "Odtwarzanie rozpoczęte",
        "toast_playback_stopped": "Odtwarzanie zatrzymane",
        "toast_playback_paused": "Odtwarzanie wstrzymane",
        "toast_playback_resumed": "Odtwarzanie wznowione",
        "toast_next_track": "Przewinięto do następnego utworu",
        "toast_prev_track": "Przewinięto do poprzedniego utworu",
        "nothing_playing": "Nic nie jest obecnie odtwarzane",
        "playback_on_other_device": "Odtwarzanie jest aktywne na {device}, nie na urządzeniu tego harmonogramu",
        "select_device": "-- Wybierz urządzenie --",
        "no_active_devices": "Nie znaleziono aktywnych urządzeń",
        "previous": "Poprzedni",
        "pause": "Pauza",
        "play": "Odtwórz",
        "stop": "Stop",
        "next": "Następny",
        "schedule": "Zaplanuj",
        "playing": "Odtwarzanie...",
        "stopping": "Zatrzymywanie...",
        "duplicate": "Duplikuj",
        "delete": "Usuń",
        "edit": "Edytuj",
        "toggle_pause": "Wstrzymaj",
        "toggle_unpause": "Wznów",
        "loading": "Ładowanie...",
        "failed_to_load": "Nie udało się załadować",
        "panel_password_prompt": "Wprowadź hasło panelu, aby kontynuować.",
        "panel_password_placeholder": "Hasło",
        "panel_login_button": "Odblokuj Panel",
        "panel_login_error": "Nieprawidłowe hasło. Spróbuj ponownie.",
        "panel_logout": "Zablokuj Panel",
        "export_schedules": "Eksport JSON",
        "import_schedules": "Import JSON",
        "test_device": "Testuj Urządzenie",
        "toast_exported": "Wyeksportowano harmonogramy",
        "toast_imported": "Zaimportowano harmonogramy",
    },
}

# ---------------------------------------------------------------------------
# Auto-generated helpers
# ---------------------------------------------------------------------------

AVAILABLE_LANGUAGES: list[str] = list(TRANSLATIONS.keys())


def _resolve_lang(lang: str) -> str:
    """Return a valid language code, falling back to Config.DEFAULT_LANGUAGE."""
    if lang in TRANSLATIONS:
        return lang
    return Config.DEFAULT_LANGUAGE if Config.DEFAULT_LANGUAGE in TRANSLATIONS else "en"


def get_translation(lang: str, key: str, **kwargs) -> str:
    """Get a translated string with fallback chain:
    requested → fallback_lang → "en" → raw key.
    """
    lang = _resolve_lang(lang)

    # 1. Try requested language
    text = TRANSLATIONS[lang].get(key)

    # 2. Try fallback language
    if text is None:
        fallback = FALLBACK_MAP.get(lang, "en")
        text = TRANSLATIONS.get(fallback, {}).get(key)

    # 3. Try English
    if text is None:
        text = TRANSLATIONS["en"].get(key)

    # 4. Fall back to the key itself
    if text is None:
        text = key

    return text.format(**kwargs) if kwargs else text


def get_all_translations(lang: str) -> dict:
    """Return the full translation dictionary for a language.
    Missing keys are back-filled from the fallback chain so the frontend
    never receives undefined values.
    """
    lang = _resolve_lang(lang)
    result = TRANSLATIONS["en"].copy()  # Start with English as base

    fallback_lang = FALLBACK_MAP.get(lang)
    if fallback_lang and fallback_lang in TRANSLATIONS:
        result.update(TRANSLATIONS[fallback_lang])

    result.update(TRANSLATIONS[lang])
    return result
