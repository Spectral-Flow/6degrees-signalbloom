"""
Configuration management for Signal Bloom Backend
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration class"""

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///signals.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

    # CORS Configuration
    CORS_ORIGINS: List[str] = json.loads(os.getenv("CORS_ORIGINS", '["*"]'))

    # Signal Configuration
    MAX_SIGNALS: int = int(os.getenv("MAX_SIGNALS", "1000"))
    MAX_SIGNAL_LENGTH: int = int(os.getenv("MAX_SIGNAL_LENGTH", "1000"))
    SIGNAL_CLEANUP_INTERVAL: int = int(os.getenv("SIGNAL_CLEANUP_INTERVAL", "3600"))

    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID: Optional[str] = os.getenv("ELEVENLABS_VOICE_ID")
    ELEVENLABS_BASE_URL: str = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []

        if cls.SECRET_KEY == "dev-secret-key-change-in-production" and not cls.DEBUG:
            errors.append("SECRET_KEY must be changed in production")

        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append("PORT must be between 1 and 65535")

        if cls.MAX_SIGNALS < 1:
            errors.append("MAX_SIGNALS must be positive")

        if cls.MAX_SIGNAL_LENGTH < 1:
            errors.append("MAX_SIGNAL_LENGTH must be positive")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return True


# Validate configuration on import
Config.validate()
