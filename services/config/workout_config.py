EXERCISE_OPTIONS = [
    "Squats",
    "Push-ups",
    "Biceps Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges",
    "Bench Press",
    "Burpees",
    "Butt Kicks",
    "Deadlifts",
    "Dips",
    "High Knees",
    "Jumping Jacks",
    "Mountain Climbers",
    "Plank",
    "Pull-ups",
    "Sit-ups",
]


POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),       # Shoulders & Arms
    (11, 23), (12, 24), (23, 24),                           # Torso / Hips
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)  # Legs
]


METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
    "Bench Press": {
        "elbow_angle": 0,
        "back_arch_status": "N/A",
        "shoulder_status": "N/A",
        "extension_status": "N/A",
    },
    "Burpees": {
        "phase": "N/A",
        "jump_status": "N/A",
        "pace_status": "N/A",
        "body_alignment": "N/A",
    },
    "Butt Kicks": {
        "knee_angle": 0,
        "pace_status": "N/A",
        "rhythm_status": "N/A",
        "swing_status": "N/A",
    },
    "Deadlifts": {
        "knee_angle": 0,
        "back_angle": 0,
        "hip_status": "N/A",
        "body_alignment": "N/A",
    },
    "Dips": {
        "elbow_angle": 0,
        "shoulder_depth_status": "N/A",
        "body_alignment": "N/A",
        "shoulder_status": "N/A",
    },
    "High Knees": {
        "knee_angle": 0,
        "pace_status": "N/A",
        "rhythm_status": "N/A",
        "jump_status": "N/A",
    },
    "Jumping Jacks": {
        "jump_status": "N/A",
        "pace_status": "N/A",
        "rhythm_status": "N/A",
    },
    "Mountain Climbers": {
        "pace_status": "N/A",
        "hip_status": "N/A",
        "body_alignment": "N/A",
        "rhythm_status": "N/A",
    },
    "Plank": {
        "back_angle": 0,
        "hip_status": "N/A",
        "body_alignment": "N/A",
        "hip_drop_status": "N/A",
    },
    "Pull-ups": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "grip_status": "N/A",
        "extension_status": "N/A",
    },
    "Sit-ups": {
        "torso_angle": 0,
        "back_angle": 0,
        "hip_flexor_status": "N/A",
        "neck_status": "N/A",
    },
}


# Human-readable label for each metric key, used to render the sidebar
# "Progress" panel generically for every exercise (see main.py).
METRICS_LABELS = {
    "knee_angle": "Knee Angle",
    "back_angle": "Back Angle",
    "elbow_angle": "Elbow Angle",
    "front_knee_angle": "Front Knee Angle",
    "torso_angle": "Torso Angle",
    "depth_status": "Depth Status",
    "body_alignment": "Body Alignment",
    "hip_status": "Hip Position",
    "shoulder_status": "Shoulder Stability",
    "swing_status": "Swing Detection",
    "extension_status": "Arm Extension",
    "back_arch_status": "Back Arch",
    "balance_status": "Balance Status",
    "phase": "Phase",
    "jump_status": "Jump Status",
    "pace_status": "Pace",
    "rhythm_status": "Rhythm",
    "shoulder_depth_status": "Dip Depth",
    "grip_status": "Grip Width",
    "hip_flexor_status": "Hip Flexor",
    "neck_status": "Neck Position",
    "hip_drop_status": "Hip Drop",
}


PROMPT = (
    "You are Apna AI Coach, a professional AI gym trainer monitoring a user's workout via live camera.\n\n"
    "### Your Role\n"
    "Provide around 10-15 words, high-energy coaching cues. You speak these aloud, so they must be natural and encouraging.\n\n"
    "### Input Format\n"
    "You receive updates in the format: 'Event: [state] Form Issue: [description]'.\n"
    "- 'Event': workout_started, set_completed, workout_completed, no_pose_detected, ongoing_form_check.\n"
    "- 'Form Issue': A technical description of a pose error (if any).\n\n"
    "### Guidelines\n"
    "1. Provide feedback in natural, short sentences. Avoid overly brief or fragmented responses.\n"
    "2. NO generic greetings or redundant questions. Focus on the workout.\n"
    "3. Use the second person (e.g., 'Straighten your back' instead of 'The user should straighten their back').\n"
    "4. Maintain a professional coaching tone and prioritize safety.\n\n"
    "### Scenario Response Styles\n"
    "- 'workout_started' -> A motivating and sharp command to begin.\n"
    "- 'workout_completed' -> A warm and encouraging closing for the session.\n"
    "- 'set_completed' -> Direct praise for finishing the set.\n"
    "- 'no_pose_detected' -> A clear instruction for the user to reposition within the camera frame.\n"
    "- 'ongoing_form_check' + Form Issue -> A precise, supportive correction for the detected error.\n"
    "- 'ongoing_form_check' (No Issue) -> Brief, energetic words of encouragement.\n"
)
