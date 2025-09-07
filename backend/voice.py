"""
ElevenLabs Voice Integration for Signal Bloom
Handles text-to-speech and conversational AI features
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional

import httpx

from config import Config

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client for ElevenLabs API integration"""

    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.base_url = Config.ELEVENLABS_BASE_URL
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.client = None
        self._initialized = False

    async def initialize(self):
        """Initialize the HTTP client"""
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured - voice features disabled")
            return

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            timeout=30.0,
        )
        self._initialized = True
        logger.info("ElevenLabs client initialized")

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("ElevenLabs client closed")

    async def is_available(self) -> bool:
        """Check if ElevenLabs service is available"""
        if not self._initialized or not self.client:
            return False

        try:
            response = await self.client.get("/v1/voices")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ElevenLabs availability check failed: {e}")
            return False

    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs TTS"""
        if not self._initialized or not self.client:
            logger.warning("ElevenLabs client not initialized")
            return None

        if not text.strip():
            return None

        voice_id = voice_id or self.voice_id
        if not voice_id:
            logger.error("No voice ID configured for TTS")
            return None

        try:
            response = await self.client.post(
                f"/v1/text-to-speech/{voice_id}",
                json={
                    "text": text.strip(),
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
                },
            )

            if response.status_code == 200:
                logger.info(f"Generated TTS for text: {text[:50]}...")
                return response.content
            else:
                logger.error(f"TTS request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None

    async def stream_text_to_speech(
        self, text: str, voice_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream text to speech for real-time playback"""
        if not self._initialized or not self.client:
            logger.warning("ElevenLabs client not initialized")
            return

        voice_id = voice_id or self.voice_id
        if not voice_id:
            logger.error("No voice ID configured for streaming TTS")
            return

        try:
            async with self.client.stream(
                "POST",
                f"/v1/text-to-speech/{voice_id}/stream",
                json={
                    "text": text.strip(),
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
                },
            ) as response:
                if response.status_code == 200:
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        yield chunk
                else:
                    logger.error(f"Streaming TTS request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")

    async def get_voices(self) -> Optional[list]:
        """Get available voices from ElevenLabs"""
        if not self._initialized or not self.client:
            return None

        try:
            response = await self.client.get("/v1/voices")
            if response.status_code == 200:
                data = response.json()
                return data.get("voices", [])
            else:
                logger.error(f"Failed to get voices: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return None


class VoiceSignalProcessor:
    """Processes voice input/output for Signal Bloom"""

    def __init__(self):
        self.elevenlabs_client = ElevenLabsClient()
        self.voice_enabled = False

    async def initialize(self):
        """Initialize voice processing"""
        await self.elevenlabs_client.initialize()
        self.voice_enabled = await self.elevenlabs_client.is_available()

        if self.voice_enabled:
            logger.info("Voice processing enabled with ElevenLabs")
        else:
            logger.info("Voice processing disabled - ElevenLabs not available")

    async def close(self):
        """Clean up voice processing resources"""
        await self.elevenlabs_client.close()

    async def process_signal_to_speech(self, signal_text: str) -> Optional[bytes]:
        """Convert a signal text to speech"""
        if not self.voice_enabled:
            return None

        # Enhance signal text for speech
        enhanced_text = self._enhance_text_for_speech(signal_text)
        return await self.elevenlabs_client.text_to_speech(enhanced_text)

    async def stream_signal_to_speech(self, signal_text: str) -> AsyncGenerator[bytes, None]:
        """Stream signal text to speech"""
        if not self.voice_enabled:
            return

        enhanced_text = self._enhance_text_for_speech(signal_text)
        async for chunk in self.elevenlabs_client.stream_text_to_speech(enhanced_text):
            yield chunk

    def _enhance_text_for_speech(self, text: str) -> str:
        """Enhance text for better speech synthesis"""
        # Add natural pauses and emphasis
        enhanced = text.strip()

        # Add pause after introductory phrases
        if enhanced.lower().startswith(("new signal", "signal", "bloom")):
            enhanced = enhanced + "..."

        # Ensure it doesn't end abruptly
        if not enhanced.endswith((".", "!", "?", "...")):
            enhanced += "."

        return enhanced

    async def get_available_voices(self) -> Optional[list]:
        """Get list of available voices"""
        return await self.elevenlabs_client.get_voices()


# Global voice processor instance
voice_processor = VoiceSignalProcessor()
