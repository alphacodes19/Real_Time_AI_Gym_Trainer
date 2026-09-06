import time
import threading
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self.last_error = None

        self._lock = threading.Lock()
        self._busy = False
        self._result = None

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
        """NON-BLOCKING. Decides whether the coach should say something and,
        if so, hands the work to a background thread. Returns immediately.

        This is called from inside Streamlit's render loop, which reruns
        roughly every 1.5s while the camera is live. The Groq LLM call and
        the gTTS call are each network round-trips taking seconds -- doing
        them inline froze the whole app (and the video feed) on every cycle.
        Results are picked up later via poll().
        """
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        is_major_event = event in ["workout_started", "set_completed", "workout_completed"]

        if not is_major_event:
            if event == "ongoing_form_check":
                # Correct a real issue fairly promptly, but don't nag -- and
                # give plain encouragement sometimes even when form is fine,
                # on a longer cooldown so it doesn't talk over every rep.
                cooldown = 8 if issue else 20
            else:
                cooldown = 8

            if now - self.last_spoken_at < cooldown:
                return None

        with self._lock:
            # Only one utterance in flight at a time. Without this, a slow
            # Groq response would let requests pile up and the coach would
            # machine-gun several queued lines at once.
            if self._busy:
                return None
            self._busy = True

        # Start the cooldown clock now (not on completion) so a slow network
        # can't cause a burst of catch-up speech afterwards.
        self.last_spoken_at = now

        worker = threading.Thread(
            target=self._generate,
            args=(event, issue),
            daemon=True,
        )
        worker.start()

        return None

    # Canned coaching lines used when the LLM can't be reached. Not as varied
    # as the generated ones, but they mean the coach still speaks with no
    # internet at all rather than going silent.
    _FALLBACK_LINES = {
        "workout_started": "Let's go. Get into position and start your first set.",
        "set_completed": "Nice work. Take your rest, then go again.",
        "workout_completed": "That's the workout done. Well done.",
        "no_pose_detected": "I can't see you. Step back into the camera frame.",
        "ongoing_form_check": "Keep going. Stay controlled and keep your form tight.",
    }

    def _fallback_text(self, event, issue):
        if issue:
            # The issue strings are written in the third person because they're
            # normally an instruction TO the LLM ("The user's back is rounding").
            # Spoken straight at the person that sounds wrong, so flip them to
            # second person and drop the coaching aside after the dash.
            text = issue.split(" -- ")[0].split(" — ")[0].strip()

            for old, new in (
                ("The user's", "Your"),
                ("The user isn't", "You aren't"),
                ("The user is not", "You are not"),
                ("The user does not", "You don't"),
                ("The user doesn't", "You don't"),
                ("The user is", "You're"),
                ("The user", "You"),
            ):
                if text.startswith(old):
                    text = new + text[len(old):]
                    break

            # Third-person possessives left over mid-sentence
            # ("You're swinging their torso" -> "your torso").
            text = text.replace(" their ", " your ").replace(" them ", " you ")

            return text

        return self._FALLBACK_LINES.get(event, "Keep going, you're doing well.")

    def _generate(self, event, issue):
        """Runs on a background thread. MUST NOT touch st.session_state --
        Streamlit session state is not available off the script thread."""
        last_exception = None

        # Retry once on transient failures. A brief connectivity blip
        # (APIConnectionError from Groq, or gTTS failing to reach Google)
        # would otherwise silently drop that coaching line entirely. This
        # runs on a background thread, so the short wait costs the user
        # nothing -- the video and rep counting are unaffected.
        for attempt in range(2):
            try:
                text = self.llm.give_feedback(event, issue)
                voice = self.tts.speak(text)

                with self._lock:
                    self._result = (voice, text)
                    self.last_error = None
                    self._busy = False

                return
            except Exception as e:
                last_exception = e

                if attempt == 0:
                    time.sleep(1.5)

        # The LLM is unreachable. Fall back to a canned line and try to speak
        # it anyway -- TextToSpeech has its own offline engine fallback, so
        # this can still produce audio with no internet at all.
        try:
            text = self._fallback_text(event, issue)
            voice = self.tts.speak(text)

            if voice:
                print(f"[VoicePipeline] LLM unreachable, used offline coaching line")

                with self._lock:
                    self._result = (voice, text)
                    self.last_error = None
                    self._busy = False

                return
        except Exception as e:
            print(f"[VoicePipeline] offline fallback also failed ({type(e).__name__}): {e}")

        # Both attempts failed. Voice coaching is a nice-to-have, so we log
        # and degrade instead of taking down rep tracking.
        print(f"[VoicePipeline] voice coaching failed ({type(last_exception).__name__}): {last_exception}")

        message = f"{type(last_exception).__name__}: {last_exception}"

        if "APIConnectionError" in type(last_exception).__name__ or "Connection" in str(last_exception):
            message = (
                "couldn't reach the coaching service (network issue). "
                "Rep counting is unaffected; the coach will resume automatically "
                "once the connection is back."
            )

        with self._lock:
            self.last_error = message
            self._busy = False

    def poll(self):
        """Called from the Streamlit script thread. Returns (audio, text)
        once a background generation has finished, else None."""
        with self._lock:
            result = self._result
            self._result = None

        return result
    

def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return
    
    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)

    # gTTS returns MP3; the offline pyttsx3 fallback returns WAV. Sniff the
    # RIFF header so the browser is told the right type either way.
    audio_format = "audio/wav" if audio_bytes[:4] == b"RIFF" else "audio/mp3"

    st.audio(audio_bytes, format=audio_format, autoplay=True)
