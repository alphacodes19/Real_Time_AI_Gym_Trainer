import os
import cv2
import av
import numpy as np
import mediapipe as mp
import threading
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from detectors import DETECTOR_REGISTRY
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False,
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        # Instantiate every detector once and keep them alive for the session.
        # Detectors maintain state (reps, stage) between frames, so we must
        # not recreate them on each recv() call.
        self._detectors: dict[str, object] = {
            name: cls() for name, cls in DETECTOR_REGISTRY.items()
        }

        self._frame_timestamp_ms = 0

    # ── thread-safe accessors ─────────────────────────────────────────────────

    def set_latest_metrics(self, metrics: dict):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self) -> dict | None:
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type: str):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self) -> str:
        with self._lock:
            return self._exercise_type

    def reset_detector(self, exercise_type: str | None = None):
        """Reset rep/stage state of one or all detectors."""
        with self._lock:
            target = exercise_type or self._exercise_type
            if target in self._detectors:
                self._detectors[target].reset()

    # ── drawing helpers ───────────────────────────────────────────────────────

    def _draw_skeleton(self, img: np.ndarray, landmarks):
        h, w = img.shape[:2]
        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 255, 0),
                    8,
                )
        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    8,
                    (255, 0, 0),
                    -1,
                )

    def _draw_no_pose_warning(self, img: np.ndarray):
        cv2.putText(img, "NO POSE DETECTED",    (30,  50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "PLEASE FACE THE CAMERA", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    def _put_text(self, img: np.ndarray, text: str, row: int = 0):
        """Helper: draw one line of overlay text anchored to the bottom-left."""
        h, _ = img.shape[:2]
        y = h - 20 - row * 40
        cv2.putText(img, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 0), 2, cv2.LINE_AA)

    # ── per-exercise overlay dispatch ─────────────────────────────────────────

    # Each method receives the full metrics dict returned by the detector and
    # draws the most relevant cues onto the frame.  A single bottom row is
    # enough for real-time feedback; the sidebar shows all numeric metrics.

    _OVERLAY_MAP: dict[str, str] = {
        "Push-ups":          "_overlay_pushup",
        "Squats":            "_overlay_squat",
        "Lunges":            "_overlay_lunge",
        "Planks":            "_overlay_plank",
        "Jumping Jacks":     "_overlay_jumping_jack",
        "Burpees":           "_overlay_burpee",
        "Mountain Climbers": "_overlay_mountain_climber",
        "Sit-ups":           "_overlay_situp",
        "Dips":              "_overlay_dip",
        "High Knees":        "_overlay_high_knee",
        "Butt Kicks":        "_overlay_butt_kick",
        "Bicep Curls":       "_overlay_bicep_curl",
        "Shoulder Press":    "_overlay_shoulder_press",
        "Bench Press":       "_overlay_bench_press",
        "Deadlifts":         "_overlay_deadlift",
        "Pull-ups":          "_overlay_pullup",
    }

    def _draw_overlays(self, img: np.ndarray, metrics: dict, ex_type: str):
        method_name = self._OVERLAY_MAP.get(ex_type)
        if method_name:
            getattr(self, method_name)(img, metrics)

    def _overlay_pushup(self, img, m):
        self._put_text(img, f"BODY: {m['body_alignment']}  |  HIP: {m['hip_status']}  |  BACK: {m['back_arch_status']}")

    def _overlay_squat(self, img, m):
        self._put_text(img, f"DEPTH: {m['depth_status']}  |  BACK: {m['back_angle']}°  |  ALIGN: {m.get('body_alignment', 'N/A')}")

    def _overlay_lunge(self, img, m):
        self._put_text(img, f"BALANCE: {m['balance_status']}  |  HIP: {m['hip_status']}  |  TORSO: {m['torso_angle']}°")

    def _overlay_plank(self, img, m):
        self._put_text(img, f"ALIGN: {m['body_alignment']}  |  HIP DROP: {m['hip_drop_status']}  |  BACK: {m['back_angle']}°")

    def _overlay_jumping_jack(self, img, m):
        self._put_text(img, f"JUMP: {m['jump_status']}  |  PACE: {m['pace_status']}  |  RHYTHM: {m['rhythm_status']}")

    def _overlay_burpee(self, img, m):
        self._put_text(img, f"PHASE: {m['phase']}  |  JUMP: {m['jump_status']}  |  PACE: {m['pace_status']}")

    def _overlay_mountain_climber(self, img, m):
        self._put_text(img, f"PACE: {m['pace_status']}  |  HIP: {m['hip_status']}  |  ALIGN: {m['body_alignment']}")

    def _overlay_situp(self, img, m):
        self._put_text(img, f"TORSO: {m['torso_angle']}°  |  NECK: {m['neck_status']}  |  HIP FLEX: {m['hip_flexor_status']}")

    def _overlay_dip(self, img, m):
        self._put_text(img, f"DEPTH: {m['shoulder_depth_status']}  |  ALIGN: {m['body_alignment']}  |  SHOULDER: {m['shoulder_status']}")

    def _overlay_high_knee(self, img, m):
        self._put_text(img, f"PACE: {m['pace_status']}  |  KNEE: {m['knee_angle']}°  |  RHYTHM: {m['rhythm_status']}")

    def _overlay_butt_kick(self, img, m):
        self._put_text(img, f"PACE: {m['pace_status']}  |  KNEE: {m['knee_angle']}°  |  SWING: {m['swing_status']}")

    def _overlay_bicep_curl(self, img, m):
        self._put_text(img, f"SWING: {m['swing_status']}  |  EXT: {m['extension_status']}  |  SHOULDER: {m['shoulder_status']}")

    def _overlay_shoulder_press(self, img, m):
        self._put_text(img, f"EXT: {m['extension_status']}  |  BACK: {m['back_arch_status']}  |  SHOULDER: {m['shoulder_status']}")

    def _overlay_bench_press(self, img, m):
        self._put_text(img, f"BACK: {m['back_arch_status']}  |  EXT: {m['extension_status']}  |  SHOULDER: {m['shoulder_status']}")

    def _overlay_deadlift(self, img, m):
        self._put_text(img, f"SPINE: {m['body_alignment']}  |  BACK: {m['back_angle']}°  |  HIP: {m['hip_status']}")

    def _overlay_pullup(self, img, m):
        self._put_text(img, f"GRIP: {m['grip_status']}  |  EXT: {m['extension_status']}  |  SHOULDER: {m['shoulder_status']}")

    # ── main frame processing loop ────────────────────────────────────────────

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image: np.ndarray = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8,
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
        )

        self._frame_timestamp_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            self._draw_skeleton(image, landmarks)

            ex_type  = self.get_exercise()
            detector = self._detectors.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True
                self._draw_overlays(image, metrics, ex_type)
                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warning(image)
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")