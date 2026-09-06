import os
import tempfile
from io import BytesIO

from gtts import gTTS


class TextToSpeech:
    """Speech synthesis with an offline fallback.

    gTTS is the primary engine (better sounding), but it needs network access
    -- it calls Google's endpoint. When there's no connectivity, it fails and
    the coach goes silent.

    pyttsx3 is used as a fallback: it drives the operating system's built-in
    speech engine (SAPI5 on Windows, NSSpeechSynthesizer on macOS, espeak on
    Linux) and works with no internet at all. It's an optional dependency --
    if it isn't installed, we simply behave as before.
    """

    def __init__(self):
        self._offline_engine_available = None

    def speak(self, text, lang="en"):
        cleaned = (text or "").strip()

        if not cleaned:
            return

        try:
            buffer = BytesIO()
            gTTS(text=cleaned, lang=lang).write_to_fp(buffer)
            buffer.seek(0)

            return buffer.read()
        except Exception as e:
            print(f"[tts] gTTS unavailable ({type(e).__name__}), trying offline engine")

            offline = self._speak_offline(cleaned)

            if offline is not None:
                return offline

            raise

    def _speak_offline(self, text):
        """Synthesize with the OS speech engine. Returns WAV bytes, or None."""
        try:
            import pyttsx3
        except ImportError:
            if self._offline_engine_available is None:
                print("[tts] pyttsx3 not installed -- no offline speech fallback. "
                      "Install it with: pip install pyttsx3")
                self._offline_engine_available = False

            return None

        path = None

        try:
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

            # A fresh engine per call: pyttsx3 engines are not reusable across
            # threads once their run loop has completed.
            engine = pyttsx3.init()
            engine.save_to_file(text, path)
            engine.runAndWait()
            engine.stop()

            with open(path, "rb") as f:
                data = f.read()

            return data if data else None
        except Exception as e:
            print(f"[tts] offline speech engine failed ({type(e).__name__}): {e}")

            return None
        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
