import streamlit as st
import os
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS, METRICS_FIELDS, METRICS_LABELS, get_rtc_configuration
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update, _safe_voice_event
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio

  

# ── Live-updating panels ─────────────────────────────────────────────────────
#
# These are st.fragment()s, NOT a full-page rerun loop.
#
# The previous version polled with `time.sleep(1.5); st.rerun()`, which reran
# the ENTIRE script every 1.5s -- including webrtc_streamer(). That destroyed
# and recreated the camera component mid-handshake, so its signalling replies
# came back to a component instance that no longer existed. That is exactly
# the flood of "Received component message for unregistered ComponentInstance!"
# console errors, and why the connection never finished negotiating.
#
# A fragment reruns only its own body on its own timer, leaving the WebRTC
# component mounted and undisturbed.

@st.fragment(run_every=1.5)
def live_progress_panel():
    """Sidebar: pulls fresh metrics off the video processor and renders them."""
    sync_metrics_update(st.session_state.get("webrtc_ctx"))

    exercise = st.session_state.get("exercise_type")

    st.subheader("Progress")

    st.metric("Total Reps", f"{st.session_state.get('reps')}")
    st.metric(
        "Current Set Reps",
        f"{st.session_state.get('current_set_reps')} / {st.session_state.get('reps_per_set')}",
    )
    st.metric(
        "Sets Completed",
        f"{st.session_state.get('sets_completed')} / {st.session_state.get('target_sets')}",
    )

    if st.session_state.get("workout_completed"):
        st.success("🎉 Workout complete — all sets done!")
    elif st.session_state.get("resting"):
        remaining = st.session_state.get("rest_remaining", 0)
        total = max(1, st.session_state.get("rest_seconds", 1))
        st.info(f"😮‍💨 Rest — {remaining}s left")
        st.progress(min(1.0, max(0.0, (total - remaining) / total)))

        if st.button("Skip rest", width="stretch", key="skip_rest_button"):
            st.session_state.rest_until = 0
            st.session_state.resting = False
            st.session_state.rest_remaining = 0

    st.divider()

    fields = METRICS_FIELDS.get(exercise, {})

    if fields:
        st.subheader(f"{exercise} Metrics")

        for field_key, default_value in fields.items():
            label = METRICS_LABELS.get(field_key, field_key.replace("_", " ").title())
            value = st.session_state.get(field_key, default_value)

            # Numeric fields (angles) default to 0 and get a degree sign;
            # status fields default to the string "N/A".
            if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
                st.metric(label, f"{value}\u00b0")
            else:
                st.metric(label, value)


@st.fragment(run_every=1.5)
def live_coach_panel():
    """Main area: picks up finished voice lines and plays them."""
    if st.session_state.get("workout_completed"):
        st.success(
            f"\U0001F389 **Workout complete!** "
            f"{st.session_state.get('sets_completed')} / {st.session_state.get('target_sets')} sets, "
            f"{st.session_state.get('reps')} total reps. "
            "Hit **End Workout** in the sidebar to finish, or keep going for extra reps."
        )

    voice_pipeline = st.session_state.get("voice_pipeline")

    if voice_pipeline:
        ready = voice_pipeline.poll()

        if ready:
            st.session_state.audio_to_play, st.session_state.coach_feedback = ready
            st.session_state.audio_started_at = time.time()

        st.session_state.voice_pipeline_error = voice_pipeline.last_error

    # A spoken line runs several seconds but this fragment refreshes every
    # 1.5s. Re-rendering the same bytes keeps the audio element mounted so
    # playback isn't cut off mid-sentence; we drop it once it's had time
    # to finish.
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

        if time.time() - st.session_state.get("audio_started_at", 0) > 15:
            st.session_state.audio_to_play = None

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"\U0001F916 **Coach:** {st.session_state.coach_feedback}")

    if st.session_state.get("voice_pipeline_error"):
        st.caption(
            f"\u26a0\ufe0f Voice coaching is temporarily unavailable: "
            f"{st.session_state.voice_pipeline_error}"
        )


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            
            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")

        if st.session_state.username:
            st.caption(f"👤 Logged in as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            plan_rest = st.number_input(
                "Rest between sets (sec)",
                min_value=0,
                max_value=300,
                key="plan_rest",
                step=5,
                help="Rep counting pauses during rest. Set to 0 to run sets back-to-back.",
            )

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.rest_seconds = int(plan_rest)
                st.session_state.reps = 0
                st.session_state._reps_floor = 0
                st.session_state._last_raw_detector_reps = 0
                st.session_state._reps_absorbed = 0
                st.session_state._reps_at_rest_start = 0
                st.session_state.rest_until = 0
                st.session_state.resting = False
                st.session_state.rest_remaining = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                _safe_voice_event("workout_started", plan_exercise, {})

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                _safe_voice_event("workout_completed", exercise, {})

                st.rerun()

        if workout_started:
            st.divider()
            live_progress_panel()

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")

    if workout_started:
        live_coach_panel()

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
            rtc_configuration=get_rtc_configuration(),
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                    "frameRate": {"ideal": 15, "max": 20},
                },
                "audio": False
            },
            async_processing=True
        )

        # Hand the live context to the auto-refreshing fragments (defined at
        # module level) so they can read metrics off the video processor
        # without the main script having to rerun.
        st.session_state["webrtc_ctx"] = context

        inject_webrtc_styles()

    st.divider()

    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()
            agg_df["Time (sec)"] = agg_df["Time (sec)"].round(1)
            agg_df.index += 1
            st.table(agg_df, border="horizontal")

            with st.expander("Per-set breakdown"):
                detail_df = df.copy()
                detail_df = detail_df.sort_values("Date", ascending=False)
                detail_df["Time (sec)"] = detail_df["Time (sec)"].round(1)
                detail_df = detail_df.rename(columns={"Sets": "Set"})
                detail_df.index = range(1, len(detail_df) + 1)
                st.dataframe(detail_df, width="stretch")
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()
    