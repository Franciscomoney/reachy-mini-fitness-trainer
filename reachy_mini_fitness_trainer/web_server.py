"""
Web Server for Reachy Mini Fitness Trainer
Handles the web UI, WebSocket connections, and pose processing
"""

import os
import json
import asyncio
import base64
import threading
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from reachy_mini import ReachyMini

from .pose_detector import PoseDetector
from .exercise_tracker import SquatTracker
from .tts_service import FitnessCoachTTS, TTSConfig
from .reachy_coach import ReachyCoach


# Global references (set by start_web_server)
_reachy_mini: Optional[ReachyMini] = None
_squat_tracker: Optional[SquatTracker] = None
_tts_service: Optional[FitnessCoachTTS] = None
_reachy_coach: Optional[ReachyCoach] = None
_pose_detector: Optional[PoseDetector] = None
_stop_event: Optional[threading.Event] = None
_active_sessions: dict = {}


app = FastAPI(
    title="Reachy Mini Fitness Trainer",
    description="AI-powered workout companion with voice coaching",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


async def send_tts_audio(websocket: WebSocket, audio: bytes, audio_format: str):
    """Send TTS audio over WebSocket as base64."""
    if audio:
        audio_b64 = base64.b64encode(audio).decode("utf-8")
        await websocket.send_json({
            "type": "audio",
            "format": audio_format,
            "data": audio_b64,
        })


@app.get("/")
async def root():
    """Serve the main UI."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Reachy Mini Fitness Trainer</h1><p>Static files not found.</p>")


@app.get("/api/status")
async def get_status():
    """Get current session status."""
    return {
        "is_active": _squat_tracker.state.is_active if _squat_tracker else False,
        "rep_count": _squat_tracker.state.rep_count if _squat_tracker else 0,
        "target_reps": _squat_tracker.target_reps if _squat_tracker else 10,
        "phase": _squat_tracker.state.phase.value if _squat_tracker else "standing",
        "progress": _squat_tracker.get_progress() if _squat_tracker else 0,
        "duration": _squat_tracker.get_duration() if _squat_tracker else 0,
        "reachy_connected": _reachy_mini is not None,
        "tts_enabled": _tts_service.is_enabled if _tts_service else False,
        "tts_provider": _tts_service.provider_name if _tts_service else None,
    }


@app.get("/api/tts/test")
async def test_tts(text: str = "Let's go! Time to work out!"):
    """Test TTS endpoint."""
    if not _tts_service or not _tts_service.is_enabled:
        return {"error": "TTS not enabled"}

    audio = await _tts_service.synthesize(text)
    if not audio:
        return {"error": "TTS synthesis failed"}

    content_type = "audio/mpeg" if _tts_service.audio_format == "mp3" else "audio/wav"
    return Response(content=audio, media_type=content_type)


@app.get("/api/reachy/status")
async def get_reachy_status():
    """Get Reachy robot status."""
    if not _reachy_mini:
        return {"connected": False}

    try:
        return {
            "connected": True,
            "head": {
                "left_antenna": _reachy_mini.head.left_antenna.present_position,
                "right_antenna": _reachy_mini.head.right_antenna.present_position,
            }
        }
    except Exception as e:
        return {"connected": True, "error": str(e)}


@app.websocket("/ws/workout")
async def workout_websocket(websocket: WebSocket):
    """WebSocket for real-time workout tracking."""
    global _pose_detector, _squat_tracker, _reachy_coach, _tts_service

    await websocket.accept()
    session_id = id(websocket)
    _active_sessions[session_id] = {
        "last_rep": 0,
        "last_phase": None,
        "last_encourage_time": asyncio.get_event_loop().time()
    }

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "frame":
                try:
                    img_data = msg["image"].split(",")[1] if "," in msg["image"] else msg["image"]
                    img_bytes = base64.b64decode(img_data)
                    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                    if img is not None and _pose_detector:
                        pose_result = _pose_detector.process_frame(img)

                        if pose_result.is_valid and _squat_tracker.state.is_active:
                            state = _squat_tracker.update(pose_result.avg_knee_angle)

                            # Check for new rep
                            if state.rep_count > _active_sessions[session_id]["last_rep"]:
                                _active_sessions[session_id]["last_rep"] = state.rep_count
                                _active_sessions[session_id]["last_encourage_time"] = asyncio.get_event_loop().time()

                                # Trigger Reachy reaction
                                if _reachy_coach:
                                    asyncio.create_task(
                                        _reachy_coach.react_to_rep(state.rep_count, state.target_reps)
                                    )

                                # Trigger TTS
                                if _tts_service and _tts_service.is_enabled:
                                    async def speak_rep():
                                        audio = await _tts_service.get_rep_audio(
                                            state.rep_count, state.target_reps
                                        )
                                        await send_tts_audio(websocket, audio, _tts_service.audio_format)
                                    asyncio.create_task(speak_rep())

                            # Periodic encouragement
                            elif _tts_service and _tts_service.is_enabled:
                                current_time = asyncio.get_event_loop().time()
                                last_encourage = _active_sessions[session_id].get("last_encourage_time", 0)
                                if current_time - last_encourage > 25:
                                    _active_sessions[session_id]["last_encourage_time"] = current_time
                                    async def speak_encourage():
                                        audio = await _tts_service.get_random_encouragement()
                                        await send_tts_audio(websocket, audio, _tts_service.audio_format)
                                    asyncio.create_task(speak_encourage())

                            await websocket.send_json({
                                "type": "pose",
                                "pose_detected": True,
                                "knee_angle": round(pose_result.avg_knee_angle, 1),
                                "phase": state.phase.value,
                                "rep_count": state.rep_count,
                                "target_reps": state.target_reps,
                                "feedback": state.feedback,
                                "progress": _squat_tracker.get_progress()
                            })
                        else:
                            await websocket.send_json({
                                "type": "pose",
                                "pose_detected": pose_result.is_valid if pose_result else False,
                                "message": "Move so camera can see your body" if not (pose_result and pose_result.is_valid) else "Ready!"
                            })

                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})

            elif msg.get("type") == "start":
                _squat_tracker.reset()
                _squat_tracker.start()
                _active_sessions[session_id]["last_rep"] = 0
                _active_sessions[session_id]["last_encourage_time"] = asyncio.get_event_loop().time()

                if _reachy_coach:
                    await _reachy_coach.watching_pose()

                await websocket.send_json({
                    "type": "started",
                    "target_reps": _squat_tracker.target_reps,
                    "tts_enabled": _tts_service.is_enabled if _tts_service else False,
                })

                # TTS welcome
                if _tts_service and _tts_service.is_enabled:
                    async def speak_start():
                        audio = await _tts_service.get_welcome_message(_squat_tracker.target_reps)
                        await send_tts_audio(websocket, audio, _tts_service.audio_format)
                    asyncio.create_task(speak_start())

            elif msg.get("type") == "stop":
                _squat_tracker.stop()
                rep_count = _squat_tracker.state.rep_count
                duration = _squat_tracker.get_duration()
                target_reached = rep_count >= _squat_tracker.target_reps

                await websocket.send_json({
                    "type": "stopped",
                    "rep_count": rep_count,
                    "duration": duration
                })

                # TTS finish
                if _tts_service and _tts_service.is_enabled:
                    async def speak_finish():
                        audio = await _tts_service.get_finish_message(rep_count, duration, target_reached)
                        await send_tts_audio(websocket, audio, _tts_service.audio_format)
                    asyncio.create_task(speak_finish())

    except WebSocketDisconnect:
        pass
    finally:
        if session_id in _active_sessions:
            del _active_sessions[session_id]


def start_web_server(
    reachy_mini: ReachyMini,
    squat_tracker: SquatTracker,
    tts_service: FitnessCoachTTS,
    stop_event: threading.Event,
    port: int = 5175
):
    """Start the web server with Reachy Mini integration."""
    global _reachy_mini, _squat_tracker, _tts_service, _reachy_coach, _pose_detector, _stop_event

    _reachy_mini = reachy_mini
    _squat_tracker = squat_tracker
    _tts_service = tts_service
    _stop_event = stop_event

    # Initialize pose detector
    _pose_detector = PoseDetector()

    # Initialize Reachy coach with direct SDK access
    _reachy_coach = ReachyCoach(reachy_mini=reachy_mini)

    # Preload TTS phrases
    if _tts_service and _tts_service.is_enabled:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_tts_service.preload_common_phrases())

    # Run uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def start_web_server_standalone(port: int = 5175):
    """Start web server without Reachy (for testing)."""
    global _squat_tracker, _tts_service, _pose_detector

    print("Starting in standalone mode (no Reachy robot)")

    target_reps = int(os.getenv("TARGET_REPS", "10"))
    _squat_tracker = SquatTracker(target_reps=target_reps)
    _pose_detector = PoseDetector()

    tts_config = TTSConfig.from_env()
    _tts_service = FitnessCoachTTS(tts_config)

    print(f"    Target Reps: {target_reps}")
    print(f"    TTS: {'✓ ' + _tts_service.provider_name if _tts_service.is_enabled else '✗ Disabled'}")
    print(f"    URL: http://localhost:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_web_server_standalone()
