"""
Speech-to-Text Service for Reachy Fitness Trainer
Uses OVH Whisper for voice command recognition
"""

import os
import base64
from typing import Optional
import httpx


class STTService:
    """
    Speech-to-Text using OVH Whisper API.
    Recognizes voice commands for exercise selection.
    """

    WHISPER_URL = "https://whisper-large-v3-turbo.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1/audio/transcriptions"

    # Keywords to match for each exercise
    EXERCISE_KEYWORDS = {
        "squats": ["squat", "squats", "squad", "squot", "legs", "leg"],
        "arm_raises": ["arm", "arms", "raise", "raises", "raised", "up", "reach", "sky"],
        "jumping_jacks": ["jump", "jumping", "jacks", "jack", "star", "cardio"]
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OVH_AI_ENDPOINTS_TOKEN")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def transcribe(self, audio_data: bytes, format: str = "webm") -> str:
        """
        Transcribe audio to text using Whisper.

        Args:
            audio_data: Raw audio bytes
            format: Audio format (webm, wav, mp3)

        Returns:
            Transcribed text
        """
        if not self.api_key:
            return ""

        client = await self._get_client()

        # Determine content type
        content_types = {
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg"
        }
        content_type = content_types.get(format, "audio/webm")

        try:
            # Send as multipart form data
            files = {
                "file": (f"audio.{format}", audio_data, content_type),
            }
            data = {
                "model": "whisper-large-v3-turbo",
                "language": "en",
                "response_format": "text"
            }

            response = await client.post(
                self.WHISPER_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                data=data
            )

            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f"STT error {response.status_code}: {response.text[:200]}")
                return ""

        except Exception as e:
            print(f"STT error: {e}")
            return ""

    def match_exercise(self, text: str) -> Optional[str]:
        """
        Match transcribed text to an exercise.

        Returns exercise key or None if no match.
        """
        if not text:
            return None

        text_lower = text.lower()

        # Check each exercise's keywords
        scores = {}
        for exercise, keywords in self.EXERCISE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[exercise] = score

        if not scores:
            return None

        # Return exercise with highest score
        return max(scores, key=scores.get)

    async def recognize_exercise(self, audio_data: bytes, format: str = "webm") -> Optional[str]:
        """
        Transcribe audio and match to an exercise.

        Returns exercise key or None.
        """
        text = await self.transcribe(audio_data, format)
        print(f"STT heard: '{text}'")

        if not text:
            return None

        exercise = self.match_exercise(text)
        if exercise:
            print(f"STT matched exercise: {exercise}")
        else:
            print(f"STT no exercise match for: '{text}'")

        return exercise

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
