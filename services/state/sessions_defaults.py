import streamlit as st

def initial_session_defaults():
    defaults = {
        # Rep & Set Tracking
        "reps": 0,
        "target_sets": 0,
        "reps_per_set": 0,
        "sets_completed": 0,
        "current_set_reps": 0,
        "workout_complete": False,
        "last_notified_sets_completed": 0,
        "last_notified_workout_complete": False,
        "last_saved_sets_completed": 0,
        "set_cycle_started_at": 0.0,
        "last_exercise_type": "Squats",

        # Workout Plan (set before starting)
        "Workout_Started": False,
        "plan_exercise": "Squats",
        "plan_sets": 3,
        "plan_reps": 10,

        # Common Angles
        "knee_angle": 0,
        "back_angle": 0,
        "elbow_angle": 0,
        "front_knee_angle": 0,
        "torso_angle": 0,
        "hip_angle": 0,
        "shoulder_angle": 0,
        "neck_angle": 0,

        # Auth
        "username": None,
        "user_id": None,

        # Status fields - Squats / Deadlifts / Lunges
        "depth_status": "N/A",
        "body_alignment": "N/A",
        "hip_status": "N/A",
        "balance_status": "N/A",

        # Status fields - Push-ups / Bench Press / Dips
        "back_arch_status": "N/A",
        "shoulder_status": "N/A",
        "extension_status": "N/A",
        "shoulder_depth_status": "N/A",

        # Status fields - Pull-ups / Bicep Curls / Shoulder Press
        "elbow_status": "N/A",
        "grip_status": "N/A",

        # Status fields - Planks
        "hip_drop_status": "N/A",

        # Status fields - Sit-ups
        "hip_flexor_status": "N/A",
        "neck_status": "N/A",

        # Status fields - Cardio (Jumping Jacks, High Knees, Butt Kicks, Mountain Climbers, Burpees)
        "jump_status": "N/A",
        "pace_status": "N/A",
        "rhythm_status": "N/A",
        "phase": "N/A",

        # Status fields - General
        "swing_status": "N/A",
        "form_status": "N/A",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
