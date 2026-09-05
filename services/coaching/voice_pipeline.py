import time
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            
            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            
            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."

            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."

            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            
            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."

            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        elif exercise == "Bench Press":
            back_arch = metrics.get("back_arch_status", "")
            shoulder = metrics.get("shoulder_status", "")

            if back_arch == "EXCESSIVE ARCH":
                return "The user's lower back is arching off the bench excessively during the bench press."

            if shoulder == "UNEVEN":
                return "The user's shoulders are uneven during the bench press — press evenly on both sides."

        elif exercise == "Burpees":
            alignment = metrics.get("body_alignment", "")

            if alignment == "POOR":
                return "The user's body is sagging during the plank phase of the burpee."

        elif exercise == "Butt Kicks":
            rhythm = metrics.get("rhythm_status", "")

            if rhythm == "IRREGULAR":
                return "The user's butt kick rhythm is irregular — encourage a steady, even pace."

        elif exercise == "Deadlifts":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "ROUNDED BACK":
                return "The user's back is rounding during the deadlift — cue them to keep the spine neutral."

            if hip_status == "TILTED":
                return "The user's hips are tilted during the deadlift — cue them to keep the hips level."

        elif exercise == "Dips":
            depth = metrics.get("shoulder_depth_status", "")
            alignment = metrics.get("body_alignment", "")

            if depth == "SHALLOW":
                return "The user isn't dipping deep enough — lower the shoulders below the elbows."

            if alignment == "LEANING":
                return "The user is leaning too far forward during the dip."

        elif exercise == "High Knees":
            rhythm = metrics.get("rhythm_status", "")

            if rhythm == "IRREGULAR":
                return "The user's high-knee rhythm is irregular — encourage a steady, even pace."

        elif exercise == "Jumping Jacks":
            rhythm = metrics.get("rhythm_status", "")

            if rhythm == "IRREGULAR":
                return "The user's jumping jack rhythm is irregular — encourage a steady, even pace."

        elif exercise == "Mountain Climbers":
            alignment = metrics.get("body_alignment", "")

            if alignment == "ROTATED":
                return "The user's hips are rotating during the mountain climber — cue them to keep the hips square."

        elif exercise == "Plank":
            alignment = metrics.get("body_alignment", "")
            hip_drop = metrics.get("hip_drop_status", "")

            if alignment == "POOR" or hip_drop == "HIPS LOW":
                return "The user's hips are sagging during the plank — cue them to engage the core."

            if hip_drop == "HIPS HIGH":
                return "The user's hips are too high during the plank — cue them to lower into a straight line."

        elif exercise == "Pull-ups":
            shoulder = metrics.get("shoulder_status", "")

            if shoulder == "UNEVEN":
                return "The user's shoulders are uneven during the pull-up — cue them to pull up evenly on both sides."

        elif exercise == "Sit-ups":
            hip_flexor = metrics.get("hip_flexor_status", "")

            if hip_flexor == "OVEREXTENDED":
                return "The user's legs are overextending during the sit-up — cue them to keep the knees bent."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        is_major_issue = event in ["workout_started", "set_completed", "workout_completed"]

        if not is_major_issue:
            if not issue:
                return None
            
            if now - self.last_spoken_at < 5:
                return None
            
        try:
            text = self.llm.give_feedback(event, issue)
            voice = self.tts.speak(text)
        except Exception:
            # The Groq LLM call and gTTS both require network access; either
            # can fail transiently (rate limit, brief outage, offline, etc.).
            # Voice coaching is a nice-to-have, not core to the workout
            # tracker, so we degrade silently instead of crashing the app.
            return None

        self.last_spoken_at = now

        return voice, text
    

def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return
    
    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)
    
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
