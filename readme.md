# 🏋️ Apna AI Coach — Real-time AI Gym Trainer

A real-time workout tracker that watches you through your webcam, counts your reps,
checks your form, and coaches you out loud while you train.

Pose estimation runs on **MediaPipe**, the video streams through **WebRTC**, and the
coaching voice comes from an **LLM + text-to-speech** pipeline — all wrapped in a
**Streamlit** app.

---

## Features

- **16 exercises** with dedicated rep-counting and form-check logic
- **Live pose overlay** — skeleton and per-exercise form status drawn onto the video
- **Automatic rep and set tracking**, with a configurable rest timer between sets
- **Proactive AI voice coaching** — encouragement while you work, corrections when your
  form slips, all generated in the background so it never stalls the video
- **Workout history** stored per user, with a per-set breakdown
- **Visibility gating** — reps are only counted when the joints an exercise depends on
  are actually being tracked, not estimated

### Supported exercises

| | | | |
|---|---|---|---|
| Squats | Push-ups | Bicep Curls | Shoulder Press |
| Lunges | Bench Press | Deadlifts | Dips |
| Pull-ups | Sit-ups | Plank | Burpees |
| Jumping Jacks | High Knees | Butt Kicks | Mountain Climbers |

---

## Requirements

> **⚠️ Python 3.9 – 3.12 (3.12 recommended).**
> `mediapipe==0.10.14` only publishes wheels for CPython 3.9–3.12. On Python 3.13 or
> 3.14 the install fails with
> `ERROR: Could not find a version that satisfies the requirement mediapipe==0.10.14`.

- A webcam
- A [Groq API key](https://console.groq.com) (free tier is fine) for voice coaching
- Internet access — the LLM and text-to-speech calls are network calls

---

## Setup

```bash
# 1. Clone
git clone https://github.com/<your-username>/real_time_ai_gym_trainer.git
cd real_time_ai_gym_trainer

# 2. Create a virtual environment on Python 3.12
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Run it:

```bash
streamlit run main.py
```

Open <http://localhost:8501>, enter a username, pick an exercise, and hit **Start Workout**.

### Linux system packages

On Linux, OpenCV needs a few shared libraries (already listed in `packages.txt`):

```bash
sudo apt-get install libgl1 libglib2.0-0t64 libsm6 libxext6
```

---

## Configuration

All optional, via `.env` (or `st.secrets` when deployed):

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | — | Required for AI voice coaching |
| `POSE_MODEL` | `pose_landmarker_full.task` | Swap in `pose_landmarker_lite.task` for lower CPU usage, or `pose_landmarker_heavy.task` for accuracy. Download from the [MediaPipe model zoo](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) into `ml_models/`. Falls back to `full` if the file is missing. |
| `TURN_URL` | — | TURN relay, only needed when deploying (see below) |
| `TURN_USERNAME` | — | TURN username |
| `TURN_CREDENTIAL` | — | TURN credential |

---

## Usage tips

**Frame your whole upper body, not just your face.** Each exercise measures specific
joints — Shoulder Press needs shoulder, elbow and wrist in shot. If those joints
aren't visible, MediaPipe only *estimates* their position, and the app will
deliberately refuse to count those reps rather than log phantom ones.

Set **Rest between sets** to `0` if you want sets to run back-to-back. While resting,
rep counting is paused so stretching or repositioning doesn't leak into your next set.

---

## Project structure

```
main.py                              Streamlit entry point and UI
core/
  base_exercise.py                   Shared angle math + landmark-visibility helper
detectors/
  __init__.py                        DETECTOR_REGISTRY: exercise name -> detector class
  <exercise>_detector.py             One rep-counting/form-check detector per exercise
services/
  auth/login_wall.py                 Username gate
  coaching/llm.py                    Groq-backed coaching text
  coaching/tts.py                    gTTS speech synthesis
  coaching/voice_pipeline.py         Background voice worker + form-issue detection
  config/workout_config.py           Exercise options, metrics, prompt, WebRTC config
  persistence/exercise_repository.py SQLite storage
  state/session_defaults.py          Session state initialisation
  tracking/metrics.py                Rep/set tracking, rest timer, history writes
  ui/style_loader.py                 CSS injection
  vision/exercise_video_processor.py WebRTC frame processing + pose detection
ml_models/                           MediaPipe .task model files
static/                             CSS and fonts
data.db                             SQLite database (auto-created)
```

### Adding a new exercise

1. Create `detectors/<name>_detector.py` subclassing `BaseExercise`, implementing
   `process(landmarks)` and `reset()`. Gate rep counting on
   `self.landmarks_visible(landmarks, ...)`.
2. Import it in `detectors/__init__.py` and add one line to `DETECTOR_REGISTRY`.
3. Add the display name to `EXERCISE_OPTIONS` and an entry to `METRICS_FIELDS` in
   `services/config/workout_config.py`.

Everything else — sidebar metrics, video overlay, session state — is driven from those
registries and needs no further changes.

---

## Architecture notes

Three details that are easy to get wrong if you refactor this:

**Voice coaching runs on a background thread.** The LLM and TTS calls each take
seconds. Running them inline in Streamlit's render path froze the app and the video
feed on every spoken line. `VoicePipeline.process_event()` returns immediately and
queues the work; `poll()` collects the result on a later cycle.

**Live panels are `st.fragment`s, not a rerun loop.** Polling with
`time.sleep(); st.rerun()` reruns the whole script, which tears down and rebuilds the
`webrtc_streamer` component mid-handshake — the WebRTC connection then never completes
(`Received component message for unregistered ComponentInstance!` in the browser
console). Fragments refresh only their own body and leave the video component mounted.

**The pose model loads lazily.** It's ~9 MB and loading it inside the video processor's
constructor delayed the WebRTC handshake enough to trigger connection timeouts. It now
loads on the first frame instead.

---

## Deploying

The app runs on Streamlit Community Cloud, with two caveats:

**Pick Python 3.12** in the *Advanced settings* dialog when you deploy. Community Cloud
defaults to a newer version that has no MediaPipe wheels. This **cannot be changed after
deployment** — you have to delete the app and redeploy it.

**You need a TURN server.** Deployed apps sit behind a proxy, so a direct
browser-to-server WebRTC connection usually fails and the video never starts. Get free
TURN credentials (e.g. [metered.ca](https://www.metered.ca/tools/openrelay/) or Xirsys)
and add them under *Settings → Secrets*:

```toml
GROQ_API_KEY = "your_key"
TURN_URL = "turn:your.turn.server:3478"
TURN_USERNAME = "your_username"
TURN_CREDENTIAL = "your_credential"
```

Also note that pose estimation runs **server-side**, so performance on free hosting
tiers will be well below what you get locally.

---

## Troubleshooting

**Video shows but there's no skeleton and reps stay at 0**

Check your terminal for:

```
AttributeError: 'MessageFactory' object has no attribute 'GetPrototype'
```

Protobuf 5.x removed a method MediaPipe still calls. Fix:

```bash
pip install "protobuf>=4.25.3,<5.0.0"
```

The app also surfaces this error in the UI with the fix command.

**"Connection is taking longer than expected"**

Locally this usually means an unreachable TURN server in the ICE config — the default
config is STUN-only for exactly this reason. Deployed, it means the opposite: you need
TURN credentials configured. Check the browser console (F12) for the real ICE error.

**No voice coaching**

The app shows a `⚠️ Voice coaching is temporarily unavailable` caption with the actual
error. Usually a missing or invalid `GROQ_API_KEY`. Rep counting keeps working
regardless — voice failures are non-fatal by design.

**`mediapipe==0.10.14` won't install**

You're on Python 3.13+. See [Requirements](#requirements).

**Laggy video**

Switch to the lite pose model via `POSE_MODEL` (see [Configuration](#configuration)).

---

## Tech stack

Streamlit · streamlit-webrtc · MediaPipe Pose Landmarker · OpenCV · Groq · gTTS · SQLite · pandas
