# ──────────────────────────────────────────────────────────────────────────────
# workout_config.py
# Central configuration for Apna AI Coach.
# ──────────────────────────────────────────────────────────────────────────────

# ── Exercise options (order matches the sidebar selectbox) ────────────────────

EXCERCISE_OPTIONS = [
    "Push-ups",
    "Squats",
    "Lunges",
    "Planks",
    "Jumping Jacks",
    "Burpees",
    "Mountain Climbers",
    "Sit-ups",
    "Dips",
    "High Knees",
    "Butt Kicks",
    "Bicep Curls",
    "Shoulder Press",
    "Bench Press",
    "Deadlifts",
    "Pull-ups",
]

# ── MediaPipe pose skeleton connections ───────────────────────────────────────
# Each tuple is (landmark_index_A, landmark_index_B).
# Reference: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

POSE_CONNECTIONS = [
    # Face / head
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    # Shoulders & arms
    (11, 12),                           # shoulder-to-shoulder
    (11, 13), (13, 15),                 # left  upper arm → forearm
    (12, 14), (14, 16),                 # right upper arm → forearm
    # Wrist landmarks (hands)
    (15, 17), (15, 19), (15, 21),
    (16, 18), (16, 20), (16, 22),
    (17, 19), (18, 20),
    # Torso
    (11, 23), (12, 24), (23, 24),
    # Legs
    (23, 25), (24, 26),                 # hip → knee
    (25, 27), (26, 28),                 # knee → ankle
    (27, 29), (28, 30),                 # ankle → heel
    (29, 31), (30, 32),                 # heel  → foot index
    (27, 31), (28, 32),                 # ankle → foot index
]

# ── Per-exercise metric fields and their default values ───────────────────────
# Used by:
#   • initial_session_defaults() to pre-populate st.session_state
#   • The video-processor callback to know which keys to push back to Streamlit

METRICS_FIELDS: dict[str, dict] = {
    "Push-ups": {
        "elbow_angle":      0,
        "body_alignment":   "N/A",
        "hip_status":       "N/A",
        "back_arch_status": "N/A",
    },
    "Squats": {
        "knee_angle":     0,
        "back_angle":     0,
        "depth_status":   "N/A",
        "body_alignment": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle":      0,
        "balance_status":   "N/A",
        "hip_status":       "N/A",
    },
    "Planks": {
        "back_angle":      0,
        "hip_status":      "N/A",
        "body_alignment":  "N/A",
        "hip_drop_status": "N/A",
    },
    "Jumping Jacks": {
        "jump_status":   "N/A",
        "pace_status":   "N/A",
        "rhythm_status": "N/A",
    },
    "Burpees": {
        "phase":          "N/A",
        "jump_status":    "N/A",
        "pace_status":    "N/A",
        "body_alignment": "N/A",
    },
    "Mountain Climbers": {
        "pace_status":    "N/A",
        "hip_status":     "N/A",
        "body_alignment": "N/A",
        "rhythm_status":  "N/A",
    },
    "Sit-ups": {
        "torso_angle":       0,
        "hip_flexor_status": "N/A",
        "neck_status":       "N/A",
        "back_angle":        0,
    },
    "Dips": {
        "elbow_angle":          0,
        "shoulder_depth_status": "N/A",
        "body_alignment":       "N/A",
        "shoulder_status":      "N/A",
    },
    "High Knees": {
        "pace_status":   "N/A",
        "knee_angle":    0,
        "rhythm_status": "N/A",
        "jump_status":   "N/A",
    },
    "Butt Kicks": {
        "pace_status":   "N/A",
        "knee_angle":    0,
        "rhythm_status": "N/A",
        "swing_status":  "N/A",
    },
    "Bicep Curls": {
        "elbow_angle":      0,
        "shoulder_status":  "N/A",
        "swing_status":     "N/A",
        "extension_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle":      0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
        "shoulder_status":  "N/A",
    },
    "Bench Press": {
        "elbow_angle":      0,
        "back_arch_status": "N/A",
        "shoulder_status":  "N/A",
        "extension_status": "N/A",
    },
    "Deadlifts": {
        "knee_angle":     0,
        "back_angle":     0,
        "hip_status":     "N/A",
        "body_alignment": "N/A",
    },
    "Pull-ups": {
        "elbow_angle":      0,
        "shoulder_status":  "N/A",
        "grip_status":      "N/A",
        "extension_status": "N/A",
    },
}

# ── AI coach system prompt ────────────────────────────────────────────────────

PROMPT = (
    "You are Apna AI Coach, a professional AI gym trainer monitoring a user's workout via live camera.\n\n"

    "### Your Role\n"
    "Provide around 10-15 words, high-energy coaching cues. "
    "You speak these aloud, so they must be natural and encouraging.\n\n"

    "### Input Format\n"
    "You receive updates in the format: 'Event: [state] Form Issue: [description]'.\n"
    "- 'Event': workout_started, set_completed, workout_completed, "
    "no_pose_detected, ongoing_form_check.\n"
    "- 'Form Issue': A technical description of a pose error (if any).\n\n"

    "### Guidelines\n"
    "1. Provide feedback in natural, short sentences. "
    "Avoid overly brief or fragmented responses.\n"
    "2. NO generic greetings or redundant questions. Focus on the workout.\n"
    "3. Use the second person "
    "(e.g., 'Straighten your back' instead of 'The user should straighten their back').\n"
    "4. Maintain a professional coaching tone and prioritize safety.\n\n"

    "### Scenario Response Styles\n"
    "- 'workout_started'   -> A motivating and sharp command to begin.\n"
    "- 'workout_completed' -> A warm and encouraging closing for the session.\n"
    "- 'set_completed'     -> Direct praise for finishing the set.\n"
    "- 'no_pose_detected'  -> A clear instruction to reposition within the camera frame.\n"
    "- 'ongoing_form_check' + Form Issue -> "
    "A precise, supportive correction for the detected error.\n"
    "- 'ongoing_form_check' (No Issue)   -> "
    "Brief, energetic words of encouragement.\n"
)

# ── Form-issue thresholds used by the voice-coaching layer ────────────────────
# These are checked against detector output to decide whether to fire a cue.
# Adjust to taste; looser = more coaching noise, tighter = quieter.

FORM_ISSUE_THRESHOLDS: dict[str, dict] = {
    "Push-ups": {
        "bad_alignment":   ["SLIGHT BEND", "POOR"],   # body_alignment values
        "bad_hip":         ["TILTED"],                 # hip_status values
        "bad_back_arch":   ["HIPS HIGH", "HIPS LOW"],  # back_arch_status values
    },
    "Squats": {
        "bad_depth":       ["TOO HIGH"],
        "bad_alignment":   ["SLIGHT ROUND", "ROUNDED BACK"],
    },
    "Lunges": {
        "bad_torso":       ["SLIGHT LEAN", "EXCESSIVE LEAN"],
        "bad_hip":         ["TILTED"],
        "bad_balance":     ["NARROW"],
    },
    "Planks": {
        "bad_alignment":   ["SLIGHT SAG", "POOR"],
        "bad_hip_drop":    ["HIPS LOW", "HIPS HIGH"],
    },
    "Jumping Jacks": {
        "bad_rhythm":      ["IRREGULAR"],
        "bad_pace":        ["SLOW"],
    },
    "Burpees": {
        "bad_alignment":   ["SLIGHT SAG", "POOR"],
        "bad_pace":        ["SLOW"],
    },
    "Mountain Climbers": {
        "bad_alignment":   ["ROTATED"],
        "bad_hip":         ["TILTED"],
        "bad_rhythm":      ["IRREGULAR"],
    },
    "Sit-ups": {
        "bad_hip_flexor":  ["OVEREXTENDED"],
        "bad_neck":        ["TUCKED"],
    },
    "Dips": {
        "bad_depth":       ["SHALLOW", "TOO HIGH"],
        "bad_alignment":   ["SLIGHT LEAN", "LEANING"],
        "bad_shoulder":    ["UNEVEN"],
    },
    "High Knees": {
        "bad_pace":        ["SLOW"],
        "bad_rhythm":      ["IRREGULAR"],
    },
    "Butt Kicks": {
        "bad_pace":        ["SLOW"],
        "bad_rhythm":      ["IRREGULAR"],
    },
    "Bicep Curls": {
        "bad_swing":       ["SWINGING"],
        "bad_extension":   ["PARTIAL"],
        "bad_shoulder":    ["RAISED"],
    },
    "Shoulder Press": {
        "bad_extension":   ["PARTIAL"],
        "bad_back_arch":   ["SLIGHT ARCH", "EXCESSIVE ARCH"],
        "bad_shoulder":    ["UNEVEN"],
    },
    "Bench Press": {
        "bad_back_arch":   ["SLIGHT ARCH", "EXCESSIVE ARCH"],
        "bad_extension":   ["PARTIAL"],
        "bad_shoulder":    ["UNEVEN"],
    },
    "Deadlifts": {
        "bad_alignment":   ["SLIGHT ROUND", "ROUNDED BACK"],
        "bad_hip":         ["TILTED"],
    },
    "Pull-ups": {
        "bad_extension":   ["PARTIAL"],
        "bad_shoulder":    ["UNEVEN"],
    },
}