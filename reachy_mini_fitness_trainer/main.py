"""
Reachy Mini Fitness Trainer - Main Application
AI-powered workout companion with voice coaching

This is a Reachy Mini App that can be published to the HuggingFace app store.
"""

import os
import asyncio
import threading
import time
from pathlib import Path
from typing import Optional

from reachy_mini import ReachyMini, ReachyMiniApp

# Import our modules
from .exercise_tracker import SquatTracker, SquatPhase
from .tts_service import FitnessCoachTTS, TTSConfig
from .web_server import start_web_server


class ReachyMiniFitnessTrainer(ReachyMiniApp):
    """
    AI Fitness Trainer for Reachy Mini

    Features:
    - Real-time pose detection and rep counting
    - Voice coaching with TTS (Inworld or OVH)
    - Reachy robot gestures and encouragement
    - Web UI for camera and stats display
    """

    # URL to the custom web UI (served by our FastAPI server)
    custom_app_url: str | None = "http://localhost:5175"

    def __init__(self):
        super().__init__()
        self.squat_tracker: Optional[SquatTracker] = None
        self.tts_service: Optional[FitnessCoachTTS] = None
        self.web_server_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        """
        Main entry point for the Reachy Mini app.

        Args:
            reachy_mini: The connected Reachy Mini instance
            stop_event: Threading event to signal graceful shutdown
        """
        print("""
        ╔═══════════════════════════════════════════════════════════════╗
        ║   💪  REACHY MINI FITNESS TRAINER  💪                         ║
        ║   Your AI-Powered Workout Companion                           ║
        ╚═══════════════════════════════════════════════════════════════╝
        """)

        # Create event loop for async operations
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            # Initialize components
            self._initialize(reachy_mini)

            # Start web server in background thread
            self._start_web_server(reachy_mini, stop_event)

            # Ready pose
            self._set_ready_pose(reachy_mini)

            print("    Fitness Trainer ready!")
            print("    Open http://localhost:5175 to start your workout")
            print("    Press Ctrl+C or stop the app to exit")

            # Main loop - keep running until stop requested
            while not stop_event.is_set():
                # The web server handles all the workout logic
                # Here we just keep the app alive and can do periodic tasks
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self._cleanup()

    def _initialize(self, reachy_mini: ReachyMini):
        """Initialize all components."""
        # Initialize exercise tracker
        target_reps = int(os.getenv("TARGET_REPS", "10"))
        self.squat_tracker = SquatTracker(target_reps=target_reps)

        # Initialize TTS
        tts_config = TTSConfig.from_env()
        self.tts_service = FitnessCoachTTS(tts_config)

        print(f"    Target Reps: {target_reps}")
        print(f"    TTS Provider: {'✓ ' + self.tts_service.provider_name if self.tts_service.is_enabled else '✗ Disabled'}")

    def _start_web_server(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        """Start the web server in a background thread."""
        def run_server():
            start_web_server(
                reachy_mini=reachy_mini,
                squat_tracker=self.squat_tracker,
                tts_service=self.tts_service,
                stop_event=stop_event,
                port=5175
            )

        self.web_server_thread = threading.Thread(target=run_server, daemon=True)
        self.web_server_thread.start()

        # Give server time to start
        time.sleep(2)

    def _set_ready_pose(self, reachy_mini: ReachyMini):
        """Set Reachy to ready/watching pose."""
        try:
            # Slight head tilt up, antennas alert
            reachy_mini.head.look_at(
                x=0.5, y=0, z=0.1,  # Look slightly up
                duration=1.0
            )
            reachy_mini.head.left_antenna.goal_position = 10
            reachy_mini.head.right_antenna.goal_position = 10
        except Exception as e:
            print(f"    Warning: Could not set ready pose: {e}")

    def _cleanup(self):
        """Cleanup resources."""
        if self.tts_service:
            # Run async cleanup in event loop
            if self._loop:
                self._loop.run_until_complete(self.tts_service.close())

        if self._loop:
            self._loop.close()

        print("    Fitness Trainer stopped. Great workout!")


# Allow running directly for testing
if __name__ == "__main__":
    import sys

    # Check if running with daemon or standalone
    if "--standalone" in sys.argv:
        # Run without Reachy (for testing web UI)
        from .web_server import start_web_server_standalone
        start_web_server_standalone()
    else:
        print("This app should be run through the Reachy Mini daemon.")
        print("Use: reachy-mini-daemon --sim")
        print("Then select this app from the dashboard.")
        print("")
        print("For standalone testing (no Reachy): python -m reachy_mini_fitness_trainer.main --standalone")
