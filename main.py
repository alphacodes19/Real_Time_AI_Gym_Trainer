import streamlit as st
import os
from services.auth.login_wall import render_login_wall
from services.state.sessions_defaults import initial_session_defaults
from services.config.workout_config import EXCERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.excercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.excercise_video_processor import VideoProcessorClass

def main():
    st.set_page_config(
        page_icon = "🏋️",
        page_title = "AI Real-Time Gym Trainer",
        layout = "centered",
        initial_sidebar_state = "expanded"
    )
    
    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "Adobeclean")
    if not render_login_wall():
        return
    
    initial_session_defaults()
    
    workout_started = st.session_state.get("Workout_Started", False)
    
    with st.sidebar:
        st.title("🏋️ Apna AI Coach")
        
        if st.session_state.username:
            st.caption(f"Login as {st.session_state.username}")
            
        st.divider()
        st.subheader("Workout Plan")
        if not workout_started:
            st.selectbox("Excercise", options=EXCERCISE_OPTIONS, key="plan_exercise")
            st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)
            st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)
            st.markdown("")
            start_session_button = st.button("Start Session", key="start_session_button")
            if start_session_button:
                st.session_state["Workout_Started"] = True
                st.rerun()
        else:
            excercise = st.session_state.get("plan_exercise")
            sets = st.session_state.get("plan_sets")
            reps = st.session_state.get("plan_reps")
            st.info(f"**{excercise}** -- {sets} Sets / {reps} Reps")
            end_session_button = st.button("End Workout", key="end_session_button")
            if end_session_button:
                st.session_state["Workout_Started"] = False
                st.rerun()
            st.divider()
            st.subheader("Progress")
            total_reps = st.session_state.get("reps", 0)
            current_set_reps = st.session_state.get("current_set_reps", 0)
            reps_per_set = st.session_state.get("plan_reps", 0)
            sets_completed = st.session_state.get("sets_completed", 0)
            target_sets = st.session_state.get("plan_sets", 0)
            st.metric("Total Reps", total_reps)
            st.metric("Current Set Reps", f"{current_set_reps}/{reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed}/{target_sets}")
            
            st.divider()
            
            if excercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)
                st.metric("Back Arch", st.session_state.back_arch_status)
                
            if excercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                
            if excercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)
                st.metric("Hip Status", st.session_state.hip_status)
                
            if excercise == "Planks":
                st.subheader("Plank Metrics")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Hip Alignment", st.session_state.hip_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Drop", st.session_state.hip_drop_status)
                
            if excercise == "Jumping Jacks":
                st.subheader("Jumping Jack Metrics")
                st.metric("Jump Status", st.session_state.jump_status)
                st.metric("Rhythm", st.session_state.rhythm_status)
                st.metric("Pace", st.session_state.pace_status)
                
            if excercise == "Burpees":
                st.subheader("Burpee Metrics")
                st.metric("Phase", st.session_state.phase)
                st.metric("Jump Status", st.session_state.jump_status)
                st.metric("Pace", st.session_state.pace_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                
            if excercise == "Mountain Climbers":
                st.subheader("Mountain Climber Metrics")
                st.metric("Pace", st.session_state.pace_status)
                st.metric("Hip Alignment", st.session_state.hip_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Rhythm", st.session_state.rhythm_status)
                
            if excercise == "Sit-ups":
                st.subheader("Sit-up Metrics")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Hip Flexor", st.session_state.hip_flexor_status)
                st.metric("Neck Status", st.session_state.neck_status)
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                
            if excercise == "Dips":
                st.subheader("Dip Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Depth", st.session_state.shoulder_depth_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Shoulder Status", st.session_state.shoulder_status)
                
            if excercise == "High Knees":
                st.subheader("High Knee Metrics")
                st.metric("Pace", st.session_state.pace_status)
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Rhythm", st.session_state.rhythm_status)
                st.metric("Jump Status", st.session_state.jump_status)
                
            if excercise == "Butt Kicks":
                st.subheader("Butt Kick Metrics")
                st.metric("Pace", st.session_state.pace_status)
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Rhythm", st.session_state.rhythm_status)
                st.metric("Swing Status", st.session_state.swing_status)
                
            if excercise == "Bicep Curls":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)
                st.metric("Extension Status", st.session_state.extension_status)
                
            if excercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)
                st.metric("Shoulder Status", st.session_state.shoulder_status)
                
            if excercise == "Bench Press":
                st.subheader("Bench Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Back Arch", st.session_state.back_arch_status)
                st.metric("Shoulder Status", st.session_state.shoulder_status)
                st.metric("Extension Status", st.session_state.extension_status)
                
            if excercise == "Deadlifts":
                st.subheader("Deadlift Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Hip Status", st.session_state.hip_status)
                st.metric("Body Alignment", st.session_state.body_alignment)
                
            if excercise == "Pull-ups":
                st.subheader("Pull-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Status", st.session_state.shoulder_status)
                st.metric("Grip Status", st.session_state.grip_status)
                st.metric("Extension Status", st.session_state.extension_status)
                
    st.title("AI Real-Time Gym Trainer")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")
    
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
            key = "excercise-analysis",
            mode= WebRtcMode.SENDRECV,
            video_processor_factory = VideoProcessorClass,
            rtc_configuration = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"video": True, "audio": False},
            async_processing = True,
        )
    st.markdown("#### Workout History")
    
    inject_webrtc_styles()
    
                
                

if __name__ == "__main__":
    main()
