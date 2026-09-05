import time
from core.base_exercise import BaseExercise


class BurpeeDetector(BaseExercise):
    """
    Burpee phases (cyclic):
        "stand" → "plank" → "pushup_down" → "pushup_up" → "jump" → "stand"

    A full rep is completed when the user returns to "stand" after "jump".
    Phase is determined by hip height (normalised y) and elbow angle.

    MediaPipe y increases downward, so a high hip = small y value.
    """

    MIN_VISIBILITY = 0.55

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_ELBOW,     RIGHT_ELBOW     = 13, 14
    LEFT_WRIST,     RIGHT_WRIST     = 15, 16
    LEFT_HIP,       RIGHT_HIP       = 23, 24
    LEFT_KNEE,      RIGHT_KNEE      = 25, 26
    LEFT_ANKLE,     RIGHT_ANKLE     = 27, 28

    # normalised-y thresholds (0 = top of frame, 1 = bottom)
    STAND_HIP_Y  = 0.55   # hips high → standing / jumping
    PLANK_HIP_Y  = 0.45   # hips low  → plank / push-up position

    PUSH_DOWN_ANGLE = 90
    PUSH_UP_ANGLE   = 150

    PACE_FAST = 4.0   # seconds per full burpee
    PACE_SLOW = 8.0

    def __init__(self):
        super().__init__()
        self._rep_times: list[float] = []
        self._last_phase = None

    def reset(self):
        self.reps        = 0
        self.stage       = None
        self._rep_times  = []
        self._last_phase = None

    def process(self, landmarks):
        # pick more-visible side
        if landmarks[self.LEFT_HIP].visibility >= landmarks[self.RIGHT_HIP].visibility:
            e_idx = self.LEFT_ELBOW
            s_idx = self.LEFT_SHOULDER
            w_idx = self.LEFT_WRIST
            h_idx = self.LEFT_HIP
            a_idx = self.LEFT_ANKLE
        else:
            e_idx = self.RIGHT_ELBOW
            s_idx = self.RIGHT_SHOULDER
            w_idx = self.RIGHT_WRIST
            h_idx = self.RIGHT_HIP
            a_idx = self.RIGHT_ANKLE

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, e_idx),
            self.get_point(landmarks, w_idx),
        )
        body_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, a_idx),
        )

        hip_y = landmarks[h_idx].y  # larger y = lower on screen

        # ── phase detection ───────────────────────────────────────────────────
        if hip_y < self.PLANK_HIP_Y:
            if elbow_angle < self.PUSH_DOWN_ANGLE:
                phase = "PUSH-UP DOWN"
            elif elbow_angle >= self.PUSH_UP_ANGLE:
                phase = "PLANK"
            else:
                phase = "PUSH-UP UP"
        elif hip_y >= self.STAND_HIP_Y:
            # wrists above shoulders → jump
            wrist_y = landmarks[w_idx].y
            sh_y    = landmarks[s_idx].y
            phase = "JUMP" if wrist_y < sh_y - 0.1 else "STAND"
        else:
            phase = "TRANSITION"

        # ── rep counting: stand→plank→jump→stand ─────────────────────────────
        if self.stage == "JUMP" and phase == "STAND":
            self.reps += 1
            self._rep_times.append(time.time())
        self.stage = phase

        # ── form metrics ─────────────────────────────────────────────────────
        body_alignment = (
            "GOOD" if body_angle >= 160
            else ("SLIGHT SAG" if body_angle >= 140 else "POOR")
        )

        jump_status = "JUMPING" if phase == "JUMP" else "GROUNDED"

        pace_status = "N/A"
        if len(self._rep_times) >= 2:
            intervals = [
                self._rep_times[i] - self._rep_times[i - 1]
                for i in range(max(1, len(self._rep_times) - 3), len(self._rep_times))
            ]
            avg = sum(intervals) / len(intervals)
            pace_status = "FAST" if avg < self.PACE_FAST else ("SLOW" if avg > self.PACE_SLOW else "MODERATE")

        return {
            "reps":           self.reps,
            "phase":          phase,
            "jump_status":    jump_status,
            "pace_status":    pace_status,
            "body_alignment": body_alignment,
        }
