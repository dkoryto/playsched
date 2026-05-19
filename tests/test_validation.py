import validation


class TestValidateSchedulePayload:
    def test_valid_full_payload(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0,1,2",
            "start_time_local": "08:00",
            "timezone": "Europe/Paris",
            "volume": 50,
            "shuffle_state": True,
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is True
        assert error is None

    def test_missing_required_fields(self):
        data = {"playlist_uri": "spotify:playlist:123"}
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "Missing required fields" in error

    def test_invalid_days_of_week(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0,1,8",
            "start_time_local": "08:00",
            "timezone": "Europe/Paris",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "days_of_week" in error.lower()

    def test_empty_days_of_week_valid(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "",
            "start_time_local": "08:00",
            "timezone": "Europe/Paris",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is True

    def test_invalid_time_format(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0",
            "start_time_local": "8:00",
            "timezone": "Europe/Paris",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "HH:MM" in error

    def test_invalid_time_values(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0",
            "start_time_local": "25:00",
            "timezone": "Europe/Paris",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "invalid time" in error.lower()

    def test_invalid_timezone(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0",
            "start_time_local": "08:00",
            "timezone": "Mars/Phobos",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "timezone" in error.lower()

    def test_volume_out_of_range(self):
        data = {
            "playlist_uri": "spotify:playlist:123",
            "target_device_id": "dev1",
            "days_of_week": "0",
            "start_time_local": "08:00",
            "timezone": "Europe/Paris",
            "volume": 101,
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "volume" in error.lower()

    def test_invalid_playlist_uri(self):
        data = {
            "playlist_uri": "not-a-spotify-uri",
            "target_device_id": "dev1",
            "days_of_week": "0",
            "start_time_local": "08:00",
            "timezone": "Europe/Paris",
        }
        is_valid, error = validation.validate_schedule_payload(data, partial=False)
        assert is_valid is False
        assert "playlist_uri" in error.lower()

    def test_partial_update_allows_missing_fields(self):
        data = {"volume": 42}
        is_valid, error = validation.validate_schedule_payload(data, partial=True)
        assert is_valid is True
        assert error is None

    def test_partial_update_validates_present_fields(self):
        data = {"volume": 999}
        is_valid, error = validation.validate_schedule_payload(data, partial=True)
        assert is_valid is False
        assert "volume" in error.lower()


class TestValidatePlaybackPayload:
    def test_valid_payload(self):
        data = {"playlist_uri": "spotify:playlist:123", "device_id": "dev1", "volume": 50}
        is_valid, error = validation.validate_playback_payload(data)
        assert is_valid is True
        assert error is None

    def test_missing_fields(self):
        data = {"playlist_uri": "spotify:playlist:123"}
        is_valid, error = validation.validate_playback_payload(data)
        assert is_valid is False
        assert "device_id" in error.lower()

    def test_invalid_uri(self):
        data = {"playlist_uri": "invalid", "device_id": "dev1"}
        is_valid, error = validation.validate_playback_payload(data)
        assert is_valid is False
        assert "playlist_uri" in error.lower()
