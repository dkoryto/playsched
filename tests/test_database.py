import database


class TestScheduleCRUD:
    def test_add_and_get_schedule(self):
        data = {
            "user_spotify_id": "user1",
            "playlist_uri": "spotify:playlist:abc",
            "playlist_name": "Test Playlist",
            "target_device_id": "device1",
            "target_device_name": "Living Room",
            "days_of_week": "1,2,3",
            "start_time_local": "08:00",
            "stop_time_local": "09:00",
            "volume": 50,
            "is_active": True,
            "timezone": "Europe/Paris",
            "shuffle_state": False,
        }
        schedule_id = database.add_schedule(data)
        assert schedule_id is not None

        fetched = database.get_schedule_by_id(schedule_id, "user1")
        assert fetched is not None
        assert fetched["playlist_uri"] == "spotify:playlist:abc"
        assert fetched["target_device_id"] == "device1"

    def test_get_all_schedules(self):
        data = {
            "user_spotify_id": "user2",
            "playlist_uri": "spotify:playlist:xyz",
            "playlist_name": "Another",
            "target_device_id": "dev2",
            "target_device_name": "Kitchen",
            "days_of_week": "",
            "start_time_local": "12:00",
            "timezone": "UTC",
        }
        database.add_schedule(data)
        schedules = database.get_all_schedules("user2")
        assert len(schedules) >= 1
        assert all(s["user_spotify_id"] == "user2" for s in schedules)

    def test_update_schedule(self):
        data = {
            "user_spotify_id": "user3",
            "playlist_uri": "spotify:playlist:old",
            "playlist_name": "Old",
            "target_device_id": "dev3",
            "target_device_name": "Bedroom",
            "days_of_week": "0",
            "start_time_local": "07:00",
            "timezone": "UTC",
        }
        sid = database.add_schedule(data)
        ok = database.update_schedule(sid, "user3", {"volume": 77, "start_time_local": "08:30"})
        assert ok is True

        fetched = database.get_schedule_by_id(sid, "user3")
        assert fetched["volume"] == 77
        assert fetched["start_time_local"] == "08:30"

    def test_delete_schedule(self):
        data = {
            "user_spotify_id": "user4",
            "playlist_uri": "spotify:playlist:del",
            "playlist_name": "To Delete",
            "target_device_id": "dev4",
            "target_device_name": "Office",
            "days_of_week": "5",
            "start_time_local": "18:00",
            "timezone": "UTC",
        }
        sid = database.add_schedule(data)
        ok = database.delete_schedule(sid, "user4")
        assert ok is True
        assert database.get_schedule_by_id(sid, "user4") is None

    def test_toggle_schedule_active(self):
        data = {
            "user_spotify_id": "user5",
            "playlist_uri": "spotify:playlist:toggle",
            "playlist_name": "Toggle",
            "target_device_id": "dev5",
            "target_device_name": "Garage",
            "days_of_week": "6",
            "start_time_local": "10:00",
            "timezone": "UTC",
        }
        sid = database.add_schedule(data)
        initial = database.get_schedule_by_id(sid, "user5")
        assert initial["is_active"] == 1

        ok = database.toggle_schedule_active(sid, "user5")
        assert ok is True
        toggled = database.get_schedule_by_id(sid, "user5")
        assert toggled["is_active"] == 0

    def test_get_active_schedules_for_scheduler(self):
        data = {
            "user_spotify_id": "user6",
            "playlist_uri": "spotify:playlist:active",
            "playlist_name": "Active",
            "target_device_id": "dev6",
            "target_device_name": "Test",
            "days_of_week": "0",
            "start_time_local": "06:00",
            "timezone": "UTC",
        }
        database.add_schedule(data)
        active = database.get_active_schedules_for_scheduler()
        assert len(active) >= 1


class TestTokenEncryption:
    def test_token_encryption_roundtrip(self):
        original_refresh = "test-refresh-token-12345"
        token_info = {
            "access_token": "access123",
            "refresh_token": original_refresh,
            "expires_at": 9999999999,
            "token_type": "Bearer",
            "scope": "user-read-private",
        }
        database.save_user_token("testuser", token_info)
        fetched = database.get_user_token("testuser")
        assert fetched is not None
        assert fetched["refresh_token"] == original_refresh
        assert fetched["access_token"] == "access123"

    def test_plaintext_fallback(self):
        # Simulate legacy plaintext token in DB by bypassing save_user_token
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_tokens "
            "(user_spotify_id, access_token, refresh_token, expires_at, token_type, scope, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("legacyuser", "acc", "plain-refresh-token", 1234567890, "Bearer", "", "2024-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()

        fetched = database.get_user_token("legacyuser")
        assert fetched is not None
        assert fetched["refresh_token"] == "plain-refresh-token"


class TestSchedulerLock:
    def test_acquire_and_release_lock(self):
        assert database.acquire_scheduler_lock("instance-a") is True
        # Same instance can re-acquire
        assert database.acquire_scheduler_lock("instance-a") is True
        # Different instance cannot acquire while lock is held
        assert database.acquire_scheduler_lock("instance-b") is False

        database.release_scheduler_lock("instance-a")
        # Now another instance can acquire
        assert database.acquire_scheduler_lock("instance-b") is True
        database.release_scheduler_lock("instance-b")

    def test_lock_ttl_expires(self):
        # Acquire with 0 TTL so it expires immediately
        assert database.acquire_scheduler_lock("inst-x", ttl_seconds=0) is True
        import time
        time.sleep(0.1)
        assert database.acquire_scheduler_lock("inst-y") is True
        database.release_scheduler_lock("inst-y")
