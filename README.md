---
title: Reachy Mini Fitness Trainer
emoji: "💪"
colorFrom: green
colorTo: blue
sdk: static
pinned: false
tags:
  - reachy_mini
  - reachy_mini_python_app
  - fitness
  - ai
  - pose-detection
  - workout
---

# Reachy Mini Fitness Trainer

> AI-powered workout companion with voice coaching for your Reachy Mini robot!

**Reachy Mini Fitness Trainer** uses MediaPipe pose detection to track your squats in real-time while Reachy Mini provides encouragement through gestures and voice coaching.

## Features

### Real-time Rep Counting
- **MediaPipe Pose Detection** - Tracks 33 body landmarks
- **Knee angle analysis** - Detects squat depth automatically
- **Works with partial body** - Just needs to see your legs
- **Automatic counting** - No manual input needed

### Voice Coaching (TTS)
- **Inworld TTS** - Fast, expressive voice (default)
- **OVH NVIDIA Riva** - Alternative high-quality TTS
- **Welcome message** - Personalized greeting when starting
- **Rep counting** - "One!", "Two!", "Three!"...
- **Encouragement** - "Halfway there!", "Almost done!"
- **Finish summary** - Stats with duration and reps

### Reachy Robot Coach
- **Head movements** - Nods on each rep
- **Antenna animations** - Wiggles when excited
- **Celebration dance** - When you hit your target
- **Watching pose** - Attentive during workout

### Animated Robot UI
- **Live robot visualization** - See Reachy react in real-time
- **Blinking eyes** - Natural idle animation
- **Antenna movement** - Synced with robot actions
- **Mood indicator** - Shows current coaching state

## Installation

### From Reachy Mini Dashboard

1. Start the Reachy Mini daemon:
   ```bash
   reachy-mini-daemon --sim  # Simulation mode
   # or
   reachy-mini-daemon        # With real robot
   ```

2. Open the dashboard at http://localhost:8000

3. Find "Fitness Trainer" in the app store and install

### Manual Installation

```bash
# Clone the repo
git clone https://github.com/Franciscomoney/reachy-mini-fitness-trainer

# Install
cd reachy-mini-fitness-trainer
pip install -e .
```

## Configuration

Create a `.env` file:

```bash
# Target reps per session
TARGET_REPS=10

# TTS Provider: "inworld" or "ovh"
TTS_PROVIDER=inworld
TTS_ENABLED=true

# Inworld TTS
INWORLD_API_KEY=your_key_here
INWORLD_VOICE=Samantha
INWORLD_MODEL=mini

# OVH TTS (alternative)
OVH_AI_ENDPOINTS_TOKEN=your_token_here
OVH_TTS_VOICE=English-US.Female-1
```

### Available Voices

**Inworld:** Samantha, Tatiana, Jennifer, Margot, Idris, Ashley, Dennis, Timothy

**OVH Riva:** English-US.Female-1 (Sofia), Female-2 (Aria), Male-1 (John)

## Usage

1. Start Reachy Mini daemon with simulation or real robot
2. Select "Fitness Trainer" from the dashboard
3. Open http://localhost:5175 in your browser
4. Click "Start Workout"
5. Allow camera access
6. Start squatting - Reachy will count!

## How It Works

### Squat Detection

```
Knee Angle = angle(hip → knee → ankle)

Standing:  angle > 160° (legs straight)
Squatting: angle < 120° (parallel or below)

Rep cycle: Standing → Down → Bottom → Up → Standing = 1 rep
```

### Tech Stack

- **Pose Detection**: MediaPipe Pose Landmarker
- **Robot Control**: Reachy Mini SDK
- **TTS**: Inworld TTS-1.5 / OVH NVIDIA Riva
- **Backend**: FastAPI + WebSockets
- **Frontend**: Vanilla JS + CSS Animations

## Project Structure

```
reachy-mini-fitness-trainer/
├── index.html                    # HuggingFace Space landing
├── pyproject.toml
├── README.md
└── reachy_mini_fitness_trainer/
    ├── __init__.py
    ├── main.py                   # ReachyMiniApp entry point
    ├── web_server.py             # FastAPI server
    ├── pose_detector.py          # MediaPipe pose detection
    ├── exercise_tracker.py       # Squat counting logic
    ├── reachy_coach.py           # Robot gestures (SDK)
    ├── tts_service.py            # Voice coaching
    └── static/
        ├── index.html            # Web UI
        ├── main.js
        └── style.css
```

## Publishing to Reachy Mini App Store

### Prerequisites
- HuggingFace account
- `reachy-mini` SDK installed with app assistant

### Step 1: Validate the App
```bash
reachy-mini-app-assistant check
```
This checks that the app structure is correct and ready for publishing.

### Step 2: Publish to HuggingFace Space
```bash
reachy-mini-app-assistant publish
```
You'll be prompted for:
- Local path to app directory
- Privacy setting (choose **public** for contest submission)

Your app will be published to:
```
https://huggingface.co/spaces/YOUR_USERNAME/reachy-mini-fitness-trainer
```

### Step 3: Submit to Official App Store (Contest Entry)
```bash
reachy-mini-app-assistant publish --official
```
This creates a PR on the [official app store dataset](https://huggingface.co/datasets/pollen-robotics/reachy-mini-official-app-store).

**Requirements for official submission:**
- App must be **public**
- Include brief description of functionality
- Subject to Pollen Robotics/HuggingFace team review

### Publishing Checklist
- [x] `ReachyMiniApp` class with `run()` method
- [x] `pyproject.toml` with package metadata
- [x] `README.md` documentation
- [x] `index.html` for HuggingFace Space landing
- [x] `custom_app_url` for web UI
- [x] Code on GitHub
- [ ] Run `reachy-mini-app-assistant check`
- [ ] Run `reachy-mini-app-assistant publish`
- [ ] Run `reachy-mini-app-assistant publish --official`

---

## Roadmap

- [x] Squat detection and counting
- [x] Voice coaching (TTS)
- [x] Reachy robot gestures
- [x] Animated robot UI
- [x] Arm raises exercise
- [x] Jumping jacks exercise
- [x] Voice-based exercise selection (STT)
- [x] Sassy motivation & teasing
- [x] Alternating head movements on reps
- [ ] Push-ups detection
- [ ] Workout history
- [ ] Multiple exercise circuits

## Authors

Created by **Francisco Cordoba Otalora** & **SAM** (Samantha AI)

## Contest Entry

Built for the **Reachy Mini App Contest 2026** by Pollen Robotics and Hugging Face.

## License

MIT License

---

*Get fit with your robot buddy!*
