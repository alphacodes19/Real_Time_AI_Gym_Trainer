import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise


def _safe_voice_event(event, exercise, metrics):
    """Call voice_pipeline.process_event defensively. Voice coaching must
    never be able to take down rep/set tracking -- whatever goes wrong here
    (a bad API key, a malformed metrics dict, anything), we log it and
    return None instead of raising."""
    voice_pipeline = st.session_state.get("voice_pipeline")

    if not voice_pipeline:
        return None

    try:
        return voice_pipeline.process_event(event=event, exercise=exercise, metrics=metrics)
    except Exception as e:
        print(f"[metrics] voice_pipeline.process_event({event!r}) failed: {type(e).__name__}: {e}")
        return None


def sync_metrics_update(context):
    if not context or not hasattr(context, "state") or not context.state.playing:
        return
    
    processor = getattr(context, "video_processor", None)

    if not processor:
        return 
    
    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return
    
    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return
    
    reps = latest_metrics.get("reps", 0)

    if reps is None:
        reps = 0

    # The video processor (and its detectors) gets recreated whenever the
    # WebRTC peer connection drops and reconnects -- a fresh detector starts
    # its internal rep counter back at 0. Without this guard, a reconnect
    # would silently wipe out reps the person already earned and the set
    # counter would appear to freeze/never advance. We keep a running
    # "floor" so total reps only ever goes up within a workout.
    prev_raw_reps = st.session_state.get("_last_raw_detector_reps", 0)

    if reps < prev_raw_reps:
        st.session_state["_reps_floor"] = st.session_state.get("_reps_floor", 0) + prev_raw_reps

    st.session_state["_last_raw_detector_reps"] = reps
    reps = st.session_state.get("_reps_floor", 0) + reps

    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return 

    for key, default in fields.items():
        st.session_state[key] = latest_metrics.get(key, default)

    reps_per_set = st.session_state.get("reps_per_set", 0)
    target_sets = st.session_state.get("target_sets", 0)

    if reps is not None and reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets 
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)

    if target_sets > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = now_ts - started_at
        user_id = st.session_state.get("user_id", 0)

        # Mark this threshold handled FIRST. If add_exercise() or the voice
        # pipeline below throws, this still can't fire again on the next
        # rerun -- otherwise a single DB/network hiccup would replay the
        # same "set completed" message and DB write every 1.5s forever.
        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

        try:
            add_exercise(user_id, exercise, newly_completed * reps_per_set, newly_completed, time_taken)
        except Exception as e:
            print(f"[metrics] failed to save exercise progress: {type(e).__name__}: {e}")

        _safe_voice_event("set_completed", exercise, latest_metrics)

    if workout_completed and not st.session_state.get("last_notified_workout_complete", False):
        st.session_state.last_notified_workout_complete = True

        _safe_voice_event("workout_completed", exercise, latest_metrics)
                
    pose_detected = latest_metrics.get("pose_detected", True)
    
    if not pose_detected and not workout_completed:
        _safe_voice_event(
            "no_pose_detected",
            exercise,
            {"issue": "No pose detected! Please step into the camera frame."},
        )

    if pose_detected and not workout_completed:
        _safe_voice_event("ongoing_form_check", exercise, latest_metrics)
