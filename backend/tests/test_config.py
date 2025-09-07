"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from config import Config


class TestConfig:
    """Test configuration management."""

    def test_default_config_values(self):
        """Test default configuration values."""
        # Test basic defaults (assuming test environment is set up)
        assert Config.HOST == "0.0.0.0"
        assert Config.PORT == 8000
        assert Config.MAX_SIGNALS == 1000
        assert Config.MAX_SIGNAL_LENGTH == 1000

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key", "DEBUG": "true"}):
            # Should not raise any exceptions
            Config.validate()

    def test_config_validation_secret_key_failure(self):
        """Test configuration validation fails with default secret key in production."""
        with patch.dict(
            os.environ, {"SECRET_KEY": "dev-secret-key-change-in-production", "DEBUG": "false"}
        ):
            with pytest.raises(ValueError, match="SECRET_KEY must be changed in production"):
                Config.validate()

    def test_config_validation_port_failure(self):
        """Test configuration validation fails with invalid port."""
        with patch.dict(os.environ, {"PORT": "99999", "SECRET_KEY": "test-secret"}):
            with pytest.raises(ValueError, match="PORT must be between 1 and 65535"):
                Config.validate()

    def test_config_max_signals_validation(self):
        """Test MAX_SIGNALS validation."""
        with patch.dict(os.environ, {"MAX_SIGNALS": "0", "SECRET_KEY": "test-secret"}):
            with pytest.raises(ValueError, match="MAX_SIGNALS must be positive"):
                Config.validate()

    def test_cors_origins_parsing(self):
        """Test CORS origins JSON parsing."""
        test_origins = '["http://localhost:3000", "http://localhost:5173"]'
        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            # Reload config to test parsing
            from importlib import reload

            import config

            reload(config)

            expected_origins = ["http://localhost:3000", "http://localhost:5173"]
            assert config.Config.CORS_ORIGINS == expected_origins

    def test_boolean_env_parsing(self):
        """Test boolean environment variable parsing."""
        with patch.dict(os.environ, {"DEBUG": "true", "DATABASE_ECHO": "false"}):
            from importlib import reload

            import config

            reload(config)

            assert config.Config.DEBUG is True
            assert config.Config.DATABASE_ECHO is False
