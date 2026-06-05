import time
from core.base_excercise import BaseExcercise


class MountainClimberDetector(BaseExcercise):
    """
    Rep logic  : alternating knee drives counted per leg.
                 Left knee drawn-in  (knee_y < hip_y - threshold) → left drive
                 Right knee drawn-in                               → right drive
                 Each drive = 0.5 rep  (two drives = one full rep).
    Body must be in plank position (hip_y < shoulder_y threshold).
    """

    MIN_VISIBILITY    = 0.55
    KNEE_DRIVE_MARGIN = 0.08   # knee must be this far above hip (in normalised y)
    PLANK_HIP_Y       = 0.55   # hip y must be below this to confirm plank position

    PACE_FAST = 0.5   # seconds per single drive
    PACE_SLOW = 1.2

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_HIP,       RIGHT_HIP       = 23, 24
    LEFT_KNEE,      RIGHT_KNEE      = 25, 26
    LEFT_ANKLE,     RIGHT_ANKLE     = 27, 28

    def __init__(self):
        super().__init__()
        self._half_reps   = 0
        self._left_state  = "out"
        self._right_state = "out"
        self._drive_times: list[float] = []

    def reset(self):
        self.reps         = 0
        self.stage        = None
        self._half_reps   = 0
        self._left_state  = "out"
        self._right_state = "out"
        self._drive_times = []

    def process(self, landmarks):
        lh_y  = landmarks[self.LEFT_HIP].y
        rh_y  = landmarks[self.RIGHT_HIP].y
        lk_y  = landmarks[self.LEFT_KNEE].y
        rk_y  = landmarks[self.RIGHT_KNEE].y
        ls_y  = landmarks[self.LEFT_SHOULDER].y
        rs_y  = landmarks[self.RIGHT_SHOULDER].y

        hip_mid_y = (lh_y + rh_y) / 2
        sh_mid_y  = (ls_y + rs_y) / 2

        # confirm plank: hips lower than PLANK_HIP_Y and roughly level with shoulders
        in_plank = hip_mid_y < self.PLANK_HIP_Y

        # ── knee drive detection ──────────────────────────────────────────────
        left_driven  = (lk_y < lh_y - self.KNEE_DRIVE_MARGIN)
        right_driven = (rk_y < rh_y - self.KNEE_DRIVE_MARGIN)

        if in_plank:
            if left_driven and self._left_state == "out":
                self._left_state = "in"
                self._half_reps += 1
                self._drive_times.append(time.time())
            elif not left_driven and self._left_state == "in":
                self._left_state = "out"

            if right_driven and self._right_state == "out":
                self._right_state = "in"
                self._half_reps += 1
                self._drive_times.append(time.time())
            elif not right_driven and self._right_state == "in":
                self._right_state = "out"

        self.reps  = self._half_reps // 2
        self.stage = "active" if in_plank else "rest"

        # ── body alignment (shoulder-hip straightness) ────────────────────────
        hip_x_diff = abs(landmarks[self.LEFT_HIP].x - landmarks[self.RIGHT_HIP].x)
        sh_x_diff  = abs(landmarks[self.LEFT_SHOULDER].x - landmarks[self.RIGHT_SHOULDER].x)
        body_alignment = "GOOD" if abs(hip_x_diff - sh_x_diff) < 0.08 else "ROTATED"

        hip_status = "LEVEL" if abs(lh_y - rh_y) < 0.04 else "TILTED"

        # pace from last 6 drives
        pace_status = "N/A"
        if len(self._drive_times) >= 2:
            n = min(len(self._drive_times), 6)
            intervals = [
                self._drive_times[i] - self._drive_times[i - 1]
                for i in range(len(self._drive_times) - n + 1, len(self._drive_times))
            ]
            avg = sum(intervals) / len(intervals)
            pace_status = "FAST" if avg < self.PACE_FAST else ("SLOW" if avg > self.PACE_SLOW else "MODERATE")

        # rhythm
        rhythm_status = "N/A"
        if len(self._drive_times) >= 4:
            intervals = [
                self._drive_times[i] - self._drive_times[i - 1]
                for i in range(len(self._drive_times) - 3, len(self._drive_times))
            ]
            variance = max(intervals) - min(intervals)
            rhythm_status = "STEADY" if variance < 0.2 else ("IRREGULAR" if variance > 0.4 else "MODERATE")

        return {
            "reps":           self.reps,
            "pace_status":    pace_status,
            "hip_status":     hip_status,
            "body_alignment": body_alignment,
            "rhythm_status":  rhythm_status,
        }