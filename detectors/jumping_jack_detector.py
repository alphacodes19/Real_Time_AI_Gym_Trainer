import time
from core.base_exercise import BaseExercise


class JumpingJackDetector(BaseExercise):
    """
    Rep logic  : arms wide (wrists outside shoulders) + legs apart → stage="open"
                 arms down + legs together                          → stage="closed" + rep
    Pace/rhythm derived from inter-rep timing.
    """

    MIN_VISIBILITY = 0.55

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_HIP,       RIGHT_HIP       = 23, 24
    LEFT_WRIST,     RIGHT_WRIST     = 15, 16
    LEFT_ANKLE,     RIGHT_ANKLE     = 27, 28

    # normalised-x thresholds (fraction of image width)
    ARM_OPEN_MARGIN  = 0.04   # wrist must be this far OUTSIDE shoulder
    LEG_OPEN_MARGIN  = 0.06   # ankle must be this far OUTSIDE hip

    PACE_FAST  = 0.9   # seconds per rep
    PACE_SLOW  = 1.8

    def __init__(self):
        super().__init__()
        self._rep_times: list[float] = []

    def reset(self):
        self.reps       = 0
        self.stage      = None
        self._rep_times = []

    def process(self, landmarks):
        lw_x  = landmarks[self.LEFT_WRIST].x
        rw_x  = landmarks[self.RIGHT_WRIST].x
        ls_x  = landmarks[self.LEFT_SHOULDER].x
        rs_x  = landmarks[self.RIGHT_SHOULDER].x
        la_x  = landmarks[self.LEFT_ANKLE].x
        ra_x  = landmarks[self.RIGHT_ANKLE].x
        lh_x  = landmarks[self.LEFT_HIP].x
        rh_x  = landmarks[self.RIGHT_HIP].x

        arms_open = (lw_x < ls_x - self.ARM_OPEN_MARGIN and
                     rw_x > rs_x + self.ARM_OPEN_MARGIN)
        legs_open = (la_x < lh_x - self.LEG_OPEN_MARGIN and
                     ra_x > rh_x + self.LEG_OPEN_MARGIN)

        arms_closed = (abs(lw_x - ls_x) < 0.12 and abs(rw_x - rs_x) < 0.12)
        legs_closed = abs(la_x - ra_x) < 0.15

        is_open   = arms_open   and legs_open
        is_closed = arms_closed and legs_closed

        # Don't advance the rep state machine off estimated joints.
        if not self.landmarks_visible(
            landmarks,
            self.LEFT_SHOULDER, self.RIGHT_SHOULDER,
            self.LEFT_WRIST, self.RIGHT_WRIST,
            self.LEFT_HIP, self.RIGHT_HIP,
            self.LEFT_ANKLE, self.RIGHT_ANKLE,
        ):
            is_open = is_closed = False

        if is_open and self.stage != "open":
            self.stage = "open"
        if is_closed and self.stage == "open":
            self.stage = "closed"
            self.reps += 1
            self._rep_times.append(time.time())

        # ── derived metrics ───────────────────────────────────────────────────
        jump_status = "IN AIR" if is_open else ("GROUNDED" if is_closed else "MOVING")

        # pace from last 4 reps
        pace_status = "N/A"
        if len(self._rep_times) >= 2:
            intervals = [
                self._rep_times[i] - self._rep_times[i - 1]
                for i in range(max(1, len(self._rep_times) - 4), len(self._rep_times))
            ]
            avg = sum(intervals) / len(intervals)
            pace_status = "FAST" if avg < self.PACE_FAST else ("SLOW" if avg > self.PACE_SLOW else "MODERATE")

        # rhythm: consistency of last 4 intervals
        rhythm_status = "N/A"
        if len(self._rep_times) >= 4:
            intervals = [
                self._rep_times[i] - self._rep_times[i - 1]
                for i in range(len(self._rep_times) - 3, len(self._rep_times))
            ]
            variance = max(intervals) - min(intervals)
            rhythm_status = "STEADY" if variance < 0.25 else ("IRREGULAR" if variance > 0.5 else "MODERATE")

        return {
            "reps":          self.reps,
            "jump_status":   jump_status,
            "pace_status":   pace_status,
            "rhythm_status": rhythm_status,
        }
