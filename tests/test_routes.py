

class TestPublicRoutes:
    def test_index_not_logged_in(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Zaloguj przez Spotify" in response.data

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"

    def test_auth_status_not_logged_in(self, client):
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["logged_in"] is False


class TestProtectedRoutesWithoutAuth:
    def test_api_schedules_unauthorized(self, client):
        response = client.get("/api/schedules")
        assert response.status_code == 401

    def test_api_playlists_unauthorized(self, client):
        response = client.get("/api/playlists")
        assert response.status_code == 401

    def test_api_devices_unauthorized(self, client):
        response = client.get("/api/devices")
        assert response.status_code == 401

    def test_api_play_now_unauthorized(self, client):
        response = client.post("/api/play_now", json={
            "playlist_uri": "spotify:playlist:test",
            "device_id": "dev1",
        })
        assert response.status_code == 401

    def test_api_current_playback_unauthorized(self, client):
        response = client.get("/api/current_playback")
        assert response.status_code == 401


class TestProtectedRoutesWithSession:
    def test_api_schedules_authorized_empty(self, client):
        with client.session_transaction() as sess:
            sess["spotify_user_id"] = "testuser"
        response = client.get("/api/schedules")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_api_add_schedule_unauthorized_when_no_token_in_db(self, client):
        with client.session_transaction() as sess:
            sess["spotify_user_id"] = "notokenuser"
        response = client.get("/api/playlists")
        # 401 because get_spotify_client returns None (no token in DB for this user)
        assert response.status_code == 401

    def test_api_toggle_schedule_not_found(self, client):
        with client.session_transaction() as sess:
            sess["spotify_user_id"] = "testuser"
        response = client.put("/api/schedules/99999/toggle")
        assert response.status_code == 404

    def test_api_play_now_unauthorized_when_no_token_in_db(self, client):
        with client.session_transaction() as sess:
            sess["spotify_user_id"] = "notokenuser"
        response = client.post("/api/play_now", json={
            "playlist_uri": "spotify:playlist:test",
            "device_id": "dev1",
        })
        assert response.status_code == 503


class TestRateLimiting:
    def test_callback_rate_limit(self, client):
        for _ in range(11):
            response = client.get("/callback")
        assert response.status_code == 429

    def test_api_rate_limit(self, client):
        with client.session_transaction() as sess:
            sess["spotify_user_id"] = "testuser"
        # Exceed 30 per minute for POST /api/schedules
        for _ in range(31):
            response = client.post("/api/schedules", json={
                "playlist_uri": "spotify:playlist:x",
                "target_device_id": "d",
                "days_of_week": "0",
                "start_time_local": "08:00",
                "timezone": "UTC",
            })
        assert response.status_code == 429


class TestI18n:
    def test_index_default_language(self, client):
        """Default language should be Polish (from DEFAULT_LANGUAGE config)."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Zaloguj przez Spotify" in response.data
        assert b"lang=\"pl\"" in response.data

    def test_index_english_via_cookie(self, client):
        """Setting 'en' cookie should render English UI."""
        client.set_cookie("lang", "en")
        response = client.get("/")
        assert response.status_code == 200
        assert b"Login with Spotify" in response.data
        assert b"lang=\"en\"" in response.data

    def test_set_language_endpoint(self, client):
        """The set_language endpoint should update the cookie."""
        response = client.post("/api/set_language", json={"lang": "en"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["lang"] == "en"
        # Cookie should be set
        assert "lang=en" in response.headers.get("Set-Cookie", "")

    def test_set_language_invalid_fallback(self, client):
        """Invalid language should fall back to DEFAULT_LANGUAGE."""
        response = client.post("/api/set_language", json={"lang": "xx"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["lang"] == "pl"  # DEFAULT_LANGUAGE

    def test_language_switcher_buttons_rendered(self, client):
        """All available languages should have buttons in the header."""
        response = client.get("/")
        assert response.status_code == 200
        assert b'data-lang="pl"' in response.data
        assert b'data-lang="en"' in response.data
        assert b"PL" in response.data
        assert b"EN" in response.data

    def test_set_language_rate_limit(self, client):
        """set_language should be rate limited."""
        for _ in range(61):
            response = client.post("/api/set_language", json={"lang": "en"})
        assert response.status_code == 429
