import streamlit as st
import os
import time
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXCERCISE_OPTIONS, METRICS_FIELDS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio


# ── Sidebar: per-exercise metric panel ───────────────────────────────────────

def _render_metrics_panel(exercise: str):
    """Render the sidebar metrics section for any exercise, driven by METRICS_FIELDS."""
    fields = METRICS_FIELDS.get(exercise, {})
    if not fields:
        return

    st.subheader(f"{exercise} Metrics")

    for key in fields:
        val = st.session_state.get(key, fields[key])
        # Angle fields end with "_angle" → append degree symbol
        label = key.replace("_", " ").title()
        if isinstance(val, (int, float)) and "angle" in key:
            st.metric(label, f"{val}°")
        else:
            st.metric(label, val)


# ── Voice pipeline initialisation ────────────────────────────────────────────

def _init_voice_pipeline():
    if "voice_pipeline" in st.session_state:
        return

    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]

        groq_client = Groq(api_key=api_key)
        st.session_state.voice_pipeline = VoicePipeline(LLMCoach(groq_client), TextToSpeech())
    except Exception:
        st.session_state.voice_pipeline = None


def _fire_voice_event(event: str, exercise: str, metrics: dict):
    """Send an event to the voice pipeline and cache audio + feedback."""
    vp = st.session_state.get("voice_pipeline")
    if not vp:
        return
    result = vp.process_event(event=event, exercise=exercise, metrics=metrics)
    if result:
        st.session_state.audio_to_play, st.session_state.coach_feedback = result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered",
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return

    initial_session_defaults()
    _init_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")

        if st.session_state.get("username"):
            st.caption(f"👤 Logged in as {st.session_state.username}")

        st.divider()
        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox(
                "Exercise", options=EXCERCISE_OPTIONS, key="plan_exercise"
            )
            plan_sets = st.number_input(
                "Sets", min_value=0, max_value=50, key="plan_sets", step=1
            )
            plan_reps = st.number_input(
                "Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1
            )
            st.markdown("")

            if st.button("Start Workout", key="start_session_button", use_container_width=True):
                st.session_state.exercise_type             = plan_exercise
                st.session_state.target_sets               = int(plan_sets)
                st.session_state.reps_per_set              = int(plan_reps)
                st.session_state.reps                      = 0
                st.session_state.current_set_reps          = 0
                st.session_state.sets_completed            = 0
                st.session_state.workout_started           = True
                st.session_state.workout_complete          = False
                st.session_state.set_cycle_started_at      = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.last_notified_sets_completed    = 0
                st.session_state.last_notified_workout_complete  = False

                _fire_voice_event("workout_started", plan_exercise, {})
                st.rerun()

        else:
            exercise = st.session_state.get("exercise_type", "")
            sets      = st.session_state.get("target_sets", 0)
            reps      = st.session_state.get("reps_per_set", 0)

            st.info(f"**{exercise}** — {sets} Sets / {reps} Reps")

            if st.button("End Workout", key="end_session_button", use_container_width=True):
                st.session_state.workout_started = False
                _fire_voice_event("workout_completed", exercise, {})
                st.rerun()

            st.divider()

            # ── Progress metrics ──────────────────────────────────────────────
            st.subheader("Progress")
            st.metric("Total Reps",       st.session_state.get("reps", 0))
            st.metric(
                "Current Set Reps",
                f"{st.session_state.get('current_set_reps', 0)} "
                f"/ {st.session_state.get('reps_per_set', 0)}",
            )
            st.metric(
                "Sets Completed",
                f"{st.session_state.get('sets_completed', 0)} "
                f"/ {st.session_state.get('target_sets', 0)}",
            )

            st.divider()

            # ── Exercise-specific metrics (driven by METRICS_FIELDS) ──────────
            _render_metrics_panel(exercise)

    # ── Main area ─────────────────────────────────────────────────────────────
    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")

    # Coach audio + feedback banner
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)
        st.session_state.audio_to_play = None          # play once then clear

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            },
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # Push current exercise choice into the video processor
        if context.video_processor:
            context.video_processor.set_exercise(
                st.session_state.get("exercise_type", "Squats")
            )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    # ── Workout history ───────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        rows = [
            {
                "Exercise":   r["exercise_name"],
                "Reps":       r["reps"],
                "Sets":       r["sets"],
                "Time (sec)": r["time"],
                "Date":       r["created_at"],
            }
            for r in history_rows
        ]

        df = pd.DataFrame(rows)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = (
                df.groupby(["Exercise", "Date"])
                .agg({"Reps": "sum", "Sets": "sum", "Time (sec)": "sum"})
                .reset_index()
            )
            agg_df.index += 1
            st.table(agg_df)
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()