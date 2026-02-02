"""
Text-to-Speech Service for Reachy Fitness Trainer
Supports both Inworld TTS and OVH NVIDIA Riva TTS with config switch.
"""

import os
import io
import base64
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

import httpx


@dataclass
class TTSConfig:
    """TTS configuration from environment."""
    provider: str  # "inworld" or "ovh"
    inworld_api_key: Optional[str] = None
    inworld_voice: str = "Samantha"
    inworld_model: str = "mini"  # "mini" or "max"
    ovh_api_key: Optional[str] = None
    ovh_voice: str = "English-US.Female-1"
    sample_rate: int = 24000
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "TTSConfig":
        """Load config from environment variables."""
        return cls(
            provider=os.getenv("TTS_PROVIDER", "inworld").lower(),
            inworld_api_key=os.getenv("INWORLD_API_KEY"),
            inworld_voice=os.getenv("INWORLD_VOICE", "Samantha"),
            inworld_model=os.getenv("INWORLD_MODEL", "mini"),
            ovh_api_key=os.getenv("OVH_AI_ENDPOINTS_TOKEN"),
            ovh_voice=os.getenv("OVH_TTS_VOICE", "English-US.Female-1"),
            sample_rate=int(os.getenv("TTS_SAMPLE_RATE", "24000")),
            enabled=os.getenv("TTS_ENABLED", "true").lower() == "true",
        )


class BaseTTSService(ABC):
    """Base class for TTS services."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio bytes (MP3)."""
        pass

    @abstractmethod
    async def close(self):
        """Cleanup resources."""
        pass


class InworldTTSService(BaseTTSService):
    """
    Inworld TTS-1.5 Service.

    Fast and cheap TTS with great quality voices.
    - TTS-1.5 Mini: <100-130ms latency, $5/1M chars
    - TTS-1.5 Max: ~200ms latency, $10/1M chars
    """

    VOICE_MAP = {
        "Samantha": "default-jdota9es7rlbjew9s1lwpw__girl2",
        "Tatiana": "default-jdota9es7rlbjew9s1lwpw__silla",
        "Jennifer": "default-jdota9es7rlbjew9s1lwpw__girl-j",
        "Margot": "default-jdota9es7rlbjew9s1lwpw__girl-m",
        "Idris": "default-jdota9es7rlbjew9s1lwpw__guy-british",
        "Ashley": "default-jdota9es7rlbjew9s1lwpw__ashley",
        "Dennis": "default-jdota9es7rlbjew9s1lwpw__dennis",
        "Timothy": "default-jdota9es7rlbjew9s1lwpw__timothy",
    }

    MODELS = {
        "mini": "inworld-tts-1",
        "max": "inworld-tts-1-max",
    }

    def __init__(
        self,
        api_key: str,
        voice: str = "Samantha",
        model: str = "mini",
        sample_rate: int = 24000,
    ):
        self.api_key = api_key
        self.base_url = "https://api.inworld.ai/tts/v1/voice:stream"
        self.voice_id = self._resolve_voice(voice)
        self.model_id = self.MODELS.get(model, self.MODELS["mini"])
        self.sample_rate = sample_rate
        self._client: Optional[httpx.AsyncClient] = None

    def _resolve_voice(self, voice: str) -> str:
        """Convert voice name to Inworld voice ID."""
        if "__" in voice:
            return voice
        return self.VOICE_MAP.get(voice, self.VOICE_MAP["Samantha"])

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to MP3 audio bytes."""
        if not text.strip():
            return b""

        client = await self._get_client()

        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "voiceId": self.voice_id,
            "modelId": self.model_id,
            "audioConfig": {
                "audioEncoding": "MP3",
                "sampleRateHertz": self.sample_rate,
                "speakingRate": 1.1,  # Slightly faster for energetic coaching
                "temperature": 1.2,   # More expressive
            },
        }

        try:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                print(f"Inworld TTS error {response.status_code}: {response.text[:200]}")
                return b""

            # Parse streaming JSON response
            audio_chunks = []
            for line in response.text.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if result := data.get("result"):
                        if audio_content := result.get("audioContent"):
                            audio_chunks.append(base64.b64decode(audio_content))
                except json.JSONDecodeError:
                    continue

            return b"".join(audio_chunks)

        except Exception as e:
            print(f"Inworld TTS error: {e}")
            return b""

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


class OVHTTSService(BaseTTSService):
    """
    OVH NVIDIA Riva TTS Service.

    Uses OVH AI Endpoints for TTS via HTTP API.
    Voices: English-US.Female-1 (Sofia), Female-2 (Aria), Male-1 (John), etc.
    """

    VOICES = {
        "Sofia": "English-US.Female-1",
        "Aria": "English-US.Female-2",
        "John": "English-US.Male-1",
        "Jason": "English-US.Male-2",
        "Leo": "English-US.Male-3",
    }

    def __init__(
        self,
        api_key: str,
        voice: str = "English-US.Female-1",
        sample_rate: int = 16000,  # OVH default
    ):
        self.api_key = api_key
        self.base_url = "https://nvr-tts-en-us.endpoints.kepler.ai.cloud.ovh.net"
        self.voice = self._resolve_voice(voice)
        self.sample_rate = sample_rate
        self._client: Optional[httpx.AsyncClient] = None

    def _resolve_voice(self, voice: str) -> str:
        """Convert voice name to OVH voice ID."""
        if voice.startswith("English-"):
            return voice
        return self.VOICES.get(voice, self.VOICES["Sofia"])

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to WAV audio bytes."""
        if not text.strip():
            return b""

        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.base_url}/api/v1/tts/text_to_audio",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "encoding": 1,  # LINEAR_PCM (WAV)
                    "language_code": "en-US",
                    "sample_rate_hz": self.sample_rate,
                    "text": text,
                    "voice_name": self.voice,
                },
            )

            if response.status_code == 200:
                return response.content
            else:
                print(f"OVH TTS error {response.status_code}: {response.text[:200]}")
                return b""

        except Exception as e:
            print(f"OVH TTS error: {e}")
            return b""

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


class FitnessCoachTTS:
    """
    TTS service for fitness coaching with pre-defined phrases.

    Caches commonly used phrases for faster playback.
    Supports both Inworld and OVH TTS backends.
    """

    # Pre-defined coaching phrases
    PHRASES = {
        # Rep counts (will be generated dynamically)
        "rep_1": "One!",
        "rep_2": "Two!",
        "rep_3": "Three!",
        "rep_4": "Four!",
        "rep_5": "Five! Great job!",
        "rep_6": "Six!",
        "rep_7": "Seven!",
        "rep_8": "Eight!",
        "rep_9": "Nine! Almost there!",
        "rep_10": "Ten! You did it!",

        # Milestones
        "halfway": "Halfway there! Keep pushing!",
        "almost": "Almost there! Just a few more!",
        "target_reached": "Amazing! You crushed it! That was incredible!",

        # Welcome messages
        "start": "Hey! Let's crush this workout together! I'll count your squats. Ready? Let's go!",
        "start_short": "Let's do this! Show me what you got!",

        # Encouragement during workout
        "good_form": "Perfect form! Keep it up!",
        "go_deeper": "Go deeper! You got this!",
        "great_depth": "Great depth! That's it!",
        "keep_going": "Keep going! You're doing amazing!",
        "push": "Push! Push! You're stronger than you think!",
        "dont_stop": "Don't stop now! Keep that momentum!",
        "feeling_it": "Feel the burn! That means it's working!",
        "youre_strong": "You're so strong! Keep pushing!",
        "almost_there": "Almost there! Dig deep!",
        "last_push": "Final push! Give it everything!",

        # Periodic encouragement (every ~30 seconds)
        "encourage_1": "Great pace! Keep it steady!",
        "encourage_2": "You're doing fantastic! Stay focused!",
        "encourage_3": "Looking strong! Don't give up!",
        "encourage_4": "Awesome work! Keep that energy up!",
        "encourage_5": "You've got this! Every rep counts!",

        # Session
        "ready": "Ready when you are! Let's make this count!",
        "finished": "Workout complete! You did amazing! Great job today!",
        "finished_target": "You hit your target! Incredible work! You should be proud!",
    }

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig.from_env()
        self._service: Optional[BaseTTSService] = None
        self._cache: dict[str, bytes] = {}
        self._cache_lock = asyncio.Lock()

    async def _get_service(self) -> BaseTTSService:
        """Get or create TTS service based on config."""
        if self._service is None:
            if self.config.provider == "inworld":
                if not self.config.inworld_api_key:
                    raise ValueError("INWORLD_API_KEY not set")
                self._service = InworldTTSService(
                    api_key=self.config.inworld_api_key,
                    voice=self.config.inworld_voice,
                    model=self.config.inworld_model,
                    sample_rate=self.config.sample_rate,
                )
                print(f"TTS: Using Inworld ({self.config.inworld_voice}, {self.config.inworld_model})")
            else:
                if not self.config.ovh_api_key:
                    raise ValueError("OVH_AI_ENDPOINTS_TOKEN not set")
                self._service = OVHTTSService(
                    api_key=self.config.ovh_api_key,
                    voice=self.config.ovh_voice,
                    sample_rate=16000,  # OVH uses 16kHz
                )
                print(f"TTS: Using OVH Riva ({self.config.ovh_voice})")
        return self._service

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio."""
        if not self.config.enabled:
            return b""

        # Check cache first
        cache_key = text.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            service = await self._get_service()
            audio = await service.synthesize(text)

            # Cache short phrases
            if len(text) < 100 and audio:
                async with self._cache_lock:
                    self._cache[cache_key] = audio

            return audio
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            return b""

    async def get_phrase(self, phrase_key: str) -> bytes:
        """Get audio for a pre-defined phrase."""
        text = self.PHRASES.get(phrase_key, phrase_key)
        return await self.synthesize(text)

    async def get_rep_audio(self, rep_count: int, target: int) -> bytes:
        """Get audio for rep count with context-aware encouragement."""
        # Build the phrase based on context
        if rep_count >= target:
            return await self.get_phrase("target_reached")
        elif rep_count == target - 1:
            return await self.synthesize(f"{rep_count}! One more!")
        elif rep_count == target - 2:
            return await self.synthesize(f"{rep_count}! Just two more!")
        elif rep_count == target - 3:
            return await self.synthesize(f"{rep_count}! Three to go!")
        elif rep_count == 5 and target >= 10:
            return await self.synthesize("Five! Halfway there!")
        elif rep_count % 5 == 0:
            return await self.synthesize(f"{rep_count}! Keep it up!")
        else:
            return await self.synthesize(f"{rep_count}!")

    async def get_form_feedback(self, feedback_type: str) -> bytes:
        """Get audio for form feedback."""
        if feedback_type == "go_deeper":
            return await self.get_phrase("go_deeper")
        elif feedback_type == "great_depth":
            return await self.get_phrase("great_depth")
        elif feedback_type == "good_form":
            return await self.get_phrase("good_form")
        return b""

    async def get_random_encouragement(self) -> bytes:
        """Get a random encouragement phrase."""
        import random
        phrases = ["encourage_1", "encourage_2", "encourage_3", "encourage_4", "encourage_5",
                   "keep_going", "youre_strong", "dont_stop"]
        return await self.get_phrase(random.choice(phrases))

    async def get_welcome_message(self, target_reps: int = 10) -> bytes:
        """Get welcome message with target info."""
        message = f"Hey! Let's crush this workout! We're doing {target_reps} squats together. I'll count every rep. Ready? Let's go!"
        return await self.synthesize(message)

    async def get_finish_message(self, rep_count: int, duration: float, target_reached: bool) -> bytes:
        """Get personalized finish message."""
        mins = int(duration // 60)
        secs = int(duration % 60)

        if target_reached:
            if mins > 0:
                message = f"Workout complete! You crushed {rep_count} reps in {mins} minutes and {secs} seconds! Incredible work!"
            else:
                message = f"Workout complete! {rep_count} reps in just {secs} seconds! You're on fire!"
        else:
            message = f"Great effort! You did {rep_count} reps. Every rep counts. Keep it up next time!"

        return await self.synthesize(message)

    async def preload_common_phrases(self):
        """Preload commonly used phrases into cache."""
        if not self.config.enabled:
            return

        print("TTS: Preloading common phrases...")
        phrases_to_load = [
            "start", "ready", "finished",
            "go_deeper", "great_depth", "push",
            "halfway", "almost", "target_reached",
        ]

        # Also preload numbers 1-10
        for i in range(1, 11):
            phrases_to_load.append(f"rep_{i}")

        for key in phrases_to_load:
            try:
                await self.get_phrase(key)
            except Exception as e:
                print(f"TTS: Failed to preload '{key}': {e}")

        print(f"TTS: Preloaded {len(self._cache)} phrases")

    async def close(self):
        """Cleanup resources."""
        if self._service:
            await self._service.close()
            self._service = None
        self._cache.clear()

    @property
    def is_enabled(self) -> bool:
        """Check if TTS is enabled and configured."""
        if not self.config.enabled:
            return False
        if self.config.provider == "inworld":
            return bool(self.config.inworld_api_key)
        return bool(self.config.ovh_api_key)

    @property
    def provider_name(self) -> str:
        """Get current provider name."""
        return self.config.provider.title()

    @property
    def audio_format(self) -> str:
        """Get audio format for current provider."""
        return "mp3" if self.config.provider == "inworld" else "wav"
