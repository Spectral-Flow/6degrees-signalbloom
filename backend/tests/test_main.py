"""Unit tests for the main application and API endpoints."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from main import create_app


class TestMainApplication:
    """Test main application functionality."""

    @pytest.fixture
    async def app(self):
        """Create test application."""
        return await create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        from starlette.testclient import TestClient

        return TestClient(app)

    def test_frontend_endpoint(self, client):
        """Test the frontend development page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Signal Bloom - Development" in response.text
        assert "WebSocket" in response.text

    def test_status_endpoint(self, client):
        """Test the health status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Signal Bloom Backend"
        assert "connections" in data
        assert "signals" in data
        assert "timestamp" in data
        assert "features" in data

    def test_voice_status_endpoint_disabled(self, client):
        """Test voice status endpoint when voice is disabled."""
        with patch("voice.voice_processor.voice_enabled", False):
            response = client.get("/voice/status")
            assert response.status_code == 200

            data = response.json()
            assert data["voice_enabled"] is False
            assert "message" in data

    def test_voice_status_endpoint_enabled(self, client):
        """Test voice status endpoint when voice is enabled."""
        mock_client = AsyncMock()
        mock_client.is_available.return_value = True
        mock_client.voice_id = "test-voice-id"

        with (
            patch("voice.voice_processor.voice_enabled", True),
            patch("voice.voice_processor.elevenlabs_client", mock_client),
            patch("voice.voice_processor.get_available_voices", return_value=["voice1", "voice2"]),
        ):

            response = client.get("/voice/status")
            assert response.status_code == 200

            data = response.json()
            assert data["voice_enabled"] is True
            assert data["voice_available"] is True
            assert data["voices_count"] == 2
            assert data["current_voice_id"] == "test-voice-id"

    def test_text_to_speech_endpoint_disabled(self, client):
        """Test TTS endpoint when voice is disabled."""
        with patch("voice.voice_processor.voice_enabled", False):
            response = client.get("/voice/tts?text=hello")
            assert response.status_code == 503

            data = response.json()
            assert "error" in data
            assert "not enabled" in data["error"]

    def test_text_to_speech_endpoint_no_text(self, client):
        """Test TTS endpoint without text parameter."""
        with patch("voice.voice_processor.voice_enabled", True):
            response = client.get("/voice/tts")
            assert response.status_code == 400

            data = response.json()
            assert "error" in data
            assert "No text provided" in data["error"]

    def test_text_to_speech_endpoint_success(self, client):
        """Test successful TTS endpoint."""
        mock_audio_data = b"fake-audio-data"

        with (
            patch("voice.voice_processor.voice_enabled", True),
            patch("voice.voice_processor.process_signal_to_speech", return_value=mock_audio_data),
        ):

            response = client.get("/voice/tts?text=hello")
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert response.content == mock_audio_data

    def test_text_to_speech_endpoint_post(self, client):
        """Test TTS endpoint with POST request."""
        mock_audio_data = b"fake-audio-data"

        with (
            patch("voice.voice_processor.voice_enabled", True),
            patch("voice.voice_processor.process_signal_to_speech", return_value=mock_audio_data),
        ):

            response = client.post("/voice/tts", json={"text": "hello world"})
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert response.content == mock_audio_data

    def test_innovation_objects_endpoint(self, client):
        """Test innovation objects listing endpoint."""
        mock_objects = [
            {"id": "obj1", "name": "Object 1", "category": "test"},
            {"id": "obj2", "name": "Object 2", "category": "test"},
        ]

        with patch("database.db_manager.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [
                type("MockObj", (), {"to_dict": lambda: obj})() for obj in mock_objects
            ]
            mock_session.execute.return_value = mock_result

            response = client.get("/api/innovation/objects")
            assert response.status_code == 200

            data = response.json()
            assert "objects" in data
            assert len(data["objects"]) == 2

    def test_innovation_tree_endpoint_missing_id(self, client):
        """Test innovation tree endpoint without object ID."""
        response = client.get("/api/innovation/tree/")
        assert response.status_code == 404  # Route not found

    def test_innovation_tree_endpoint_success(self, client):
        """Test successful innovation tree retrieval."""
        mock_tree = {"id": "test-obj", "name": "Test Object", "category": "test", "children": []}

        with patch("database.db_manager.get_innovation_tree", return_value=mock_tree):
            response = client.get("/api/innovation/tree/test-obj")
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == "test-obj"
            assert data["name"] == "Test Object"

    def test_innovation_tree_endpoint_not_found(self, client):
        """Test innovation tree endpoint with non-existent object."""
        with patch("database.db_manager.get_innovation_tree", return_value=None):
            response = client.get("/api/innovation/tree/nonexistent")
            assert response.status_code == 404

            data = response.json()
            assert "error" in data
            assert "not found" in data["error"]


class TestWebSocketEndpoints:
    """Test WebSocket functionality."""

    @pytest.fixture
    async def app(self):
        """Create test application."""
        return await create_app()

    def test_websocket_connection(self, app):
        """Test WebSocket connection."""
        from starlette.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Connection should be established
                assert websocket is not None

    def test_websocket_signal_broadcast(self, app):
        """Test signal broadcasting through WebSocket."""
        from starlette.testclient import TestClient

        test_signal = {"type": "signal", "text": "Test WebSocket signal", "x": 50.0, "y": 75.0}

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send a signal
                websocket.send_json(test_signal)

                # Should receive the broadcasted signal back
                data = websocket.receive_json()
                assert data["type"] == "signal"
                assert data["text"] == "Test WebSocket signal"
                assert "id" in data
                assert "timestamp" in data

    def test_websocket_invalid_json(self, app):
        """Test WebSocket with invalid JSON."""
        from starlette.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send invalid JSON
                websocket.send_text("invalid json")

                # Should receive error message
                data = websocket.receive_json()
                assert data["type"] == "error"
                assert "Invalid JSON" in data["message"]

    def test_websocket_unknown_message_type(self, app):
        """Test WebSocket with unknown message type."""
        from starlette.testclient import TestClient

        unknown_message = {"type": "unknown", "data": "test"}

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send unknown message type
                websocket.send_json(unknown_message)

                # WebSocket should remain connected (just log warning)
                # Send a valid signal to verify connection is still active
                valid_signal = {
                    "type": "signal",
                    "text": "Valid signal after unknown message",
                    "x": 25.0,
                    "y": 25.0,
                }
                websocket.send_json(valid_signal)

                data = websocket.receive_json()
                assert data["type"] == "signal"
                assert data["text"] == "Valid signal after unknown message"
