import streamlit as st


def initial_session_defaults():
    defaults = {
        # Rep & Set Tracking
        "reps": 0,
        "target_sets": 0,
        "reps_per_set": 0,
        "sets_completed": 0,
        "current_set_reps": 0,
        "workout_completed": False,
        "last_notified_sets_completed": 0,
        "last_notified_workout_complete": False,
        "last_saved_sets_completed": 0,
        "set_cycle_started_at": 0.0,
        "last_exercise_type": "Squats",
        "_reps_floor": 0,
        "_last_raw_detector_reps": 0,

        # Workout plan (set before starting)
        "workout_started": False,
        "plan_exercise": "Squats",
        "plan_sets": 3,
        "plan_reps": 10,

        # Angles (shared across exercises)
        "knee_angle": 0,
        "back_angle": 0,
        "elbow_angle": 0,
        "front_knee_angle": 0,
        "torso_angle": 0,

        # Status fields (shared across exercises)
        "depth_status": "N/A",
        "body_alignment": "N/A",
        "hip_status": "N/A",
        "shoulder_status": "N/A",
        "swing_status": "N/A",
        "extension_status": "N/A",
        "back_arch_status": "N/A",
        "balance_status": "N/A",

        # Status fields - added for Bench Press / Burpees / Butt Kicks / Deadlifts /
        # Dips / High Knees / Jumping Jacks / Mountain Climbers / Plank / Pull-ups / Sit-ups
        "phase": "N/A",
        "jump_status": "N/A",
        "pace_status": "N/A",
        "rhythm_status": "N/A",
        "shoulder_depth_status": "N/A",
        "grip_status": "N/A",
        "hip_flexor_status": "N/A",
        "neck_status": "N/A",
        "hip_drop_status": "N/A",

        # Voice coaching
        "audio_to_play": None,
        "audio_started_at": 0.0,
        "coach_feedback": None,
        "voice_pipeline_error": None,

        # Active workout state
        "exercise_type": "Squats",
        "username": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
