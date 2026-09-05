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

        # The pose model is ~9MB and takes a second or more to load. This
        # constructor runs while the WebRTC connection is still being
        # negotiated, so loading it here delays the handshake and can push
        # the browser into "Connection is taking longer than expected".
        # We defer it to the first frame instead -- negotiation finishes
        # immediately and the model loads while video is already flowing.
        self._landmarker = None

        # Instantiate every registered detector once and keep it alive for the
        # whole session -- detectors carry rep/stage state between frames, so
        # they must not be recreated on every recv() call.
        self._detectors = {
            name: detector_cls() for name, detector_cls in DETECTOR_REGISTRY.items()
        }

        self._frame_timestamps_ms = 0

    def _get_landmarker(self):
        if self._landmarker is None:
            model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
            base_option = python.BaseOptions(model_asset_path=model_path)

            options = vision.PoseLandmarkerOptions(
                base_options=base_option,
                running_mode=vision.RunningMode.VIDEO,
                min_pose_detection_confidence=0.7,
                min_pose_presence_confidence=0.7,
                min_tracking_confidence=0.7,
                output_segmentation_masks=False
            )

            self._landmarker = vision.PoseLandmarker.create_from_options(options)

        return self._landmarker

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def reset_detector(self, exercise_type=None):
        """Reset rep/stage state of one detector (or the active one)."""
        with self._lock:
            target = exercise_type or self._exercise_type
            if target in self._detectors:
                self._detectors[target].reset()

    def _draw_skeleton(self, img, landmarks):
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
                    8
                )
        
        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img, 
                    (int(lm.x * w), int(lm.y * h)),
                    8,
                    (255, 0, 0),
                    -1
                )
            
    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def _put_overlay_text(self, img, text):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            text,
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    # ── per-exercise overlay dispatch ───────────────────────────────────────
    # Each entry maps an exercise name to the metric keys (in the order they
    # should appear) drawn as one status line at the bottom of the frame.
    # Using .get(...) with a fallback means a missing/renamed metric key can
    # never crash frame processing -- it just prints "N/A" for that field.

    _OVERLAY_FIELDS = {
        "Squats": ["depth_status"],
        "Push-ups": ["body_alignment", "hip_status"],
        "Biceps Curls (Dumbbell)": ["swing_status"],
        "Shoulder Press": ["extension_status", "back_arch_status"],
        "Lunges": ["balance_status"],
        "Bench Press": ["back_arch_status", "extension_status", "shoulder_status"],
        "Burpees": ["phase", "jump_status", "pace_status"],
        "Butt Kicks": ["pace_status", "rhythm_status", "swing_status"],
        "Deadlifts": ["body_alignment", "hip_status"],
        "Dips": ["shoulder_depth_status", "body_alignment"],
        "High Knees": ["pace_status", "rhythm_status", "jump_status"],
        "Jumping Jacks": ["jump_status", "pace_status", "rhythm_status"],
        "Mountain Climbers": ["pace_status", "body_alignment", "hip_status"],
        "Plank": ["body_alignment", "hip_drop_status"],
        "Pull-ups": ["grip_status", "extension_status", "shoulder_status"],
        "Sit-ups": ["hip_flexor_status", "neck_status"],
    }

    _FIELD_TAGS = {
        "depth_status": "DEPTH",
        "body_alignment": "BODY",
        "hip_status": "HIP",
        "swing_status": "SWING",
        "extension_status": "EXT",
        "back_arch_status": "BACK",
        "balance_status": "BALANCE",
        "shoulder_status": "SHOULDER",
        "phase": "PHASE",
        "jump_status": "JUMP",
        "pace_status": "PACE",
        "rhythm_status": "RHYTHM",
        "shoulder_depth_status": "DEPTH",
        "grip_status": "GRIP",
        "hip_flexor_status": "HIP FLEX",
        "neck_status": "NECK",
        "hip_drop_status": "HIP DROP",
    }

    def _draw_overlays(self, img, metrics, ex_type):
        fields = self._OVERLAY_FIELDS.get(ex_type)

        if not fields:
            return

        parts = [
            f"{self._FIELD_TAGS.get(field, field.upper())}: {metrics.get(field, 'N/A')}"
            for field in fields
        ]

        self._put_overlay_text(img, " | ".join(parts))

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        )

        self._frame_timestamps_ms += 30
        result = self._get_landmarker().detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            self._draw_skeleton(image, landmarks)

            ex_type = self.get_exercise()

            detector = self._detectors.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)

                metrics["pose_detected"] = True

                self._draw_overlays(image, metrics, ex_type)

                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warnings(image)
            
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")
