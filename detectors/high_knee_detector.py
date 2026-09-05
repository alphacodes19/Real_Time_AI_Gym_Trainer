import time
from core.base_exercise import BaseExercise


class HighKneeDetector(BaseExercise):
    """
    Rep logic  : alternating knee raises.
                 Knee y < hip y − margin → "raised"; returning = 0.5 rep each.
    """

    KNEE_RAISE_MARGIN = 0.07   # knee must be this far above hip (normalised y)
    MIN_VISIBILITY    = 0.55
    PACE_FAST = 0.4
    PACE_SLOW = 1.0

    LEFT_HIP,   RIGHT_HIP   = 23, 24
    LEFT_KNEE,  RIGHT_KNEE  = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28

    def __init__(self):
        super().__init__()
        self._half_reps   = 0
        self._left_state  = "down"
        self._right_state = "down"
        self._raise_times: list[float] = []

    def reset(self):
        self.reps          = 0
        self.stage         = None
        self._half_reps    = 0
        self._left_state   = "down"
        self._right_state  = "down"
        self._raise_times  = []

    def process(self, landmarks):
        lh_y = landmarks[self.LEFT_HIP].y
        rh_y = landmarks[self.RIGHT_HIP].y
        lk_y = landmarks[self.LEFT_KNEE].y
        rk_y = landmarks[self.RIGHT_KNEE].y
        la_y = landmarks[self.LEFT_ANKLE].y
        ra_y = landmarks[self.RIGHT_ANKLE].y

        left_raised  = lk_y < lh_y - self.KNEE_RAISE_MARGIN
        right_raised = rk_y < rh_y - self.KNEE_RAISE_MARGIN

        if left_raised and self._left_state == "down":
            self._left_state = "up"
            self._half_reps += 1
            self._raise_times.append(time.time())
        elif not left_raised and self._left_state == "up":
            self._left_state = "down"

        if right_raised and self._right_state == "down":
            self._right_state = "up"
            self._half_reps += 1
            self._raise_times.append(time.time())
        elif not right_raised and self._right_state == "up":
            self._right_state = "down"

        self.reps  = self._half_reps // 2
        self.stage = "active"

        # knee angle of the raised leg for the metric
        if left_raised:
            knee_angle = self.calculate_angle(
                self.get_point(landmarks, self.LEFT_HIP),
                self.get_point(landmarks, self.LEFT_KNEE),
                self.get_point(landmarks, self.LEFT_ANKLE),
            )
        elif right_raised:
            knee_angle = self.calculate_angle(
                self.get_point(landmarks, self.RIGHT_HIP),
                self.get_point(landmarks, self.RIGHT_KNEE),
                self.get_point(landmarks, self.RIGHT_ANKLE),
            )
        else:
            knee_angle = 180

        jump_status = "RAISED" if (left_raised or right_raised) else "GROUNDED"

        pace_status = "N/A"
        if len(self._raise_times) >= 2:
            n = min(len(self._raise_times), 6)
            intervals = [
                self._raise_times[i] - self._raise_times[i - 1]
                for i in range(len(self._raise_times) - n + 1, len(self._raise_times))
            ]
            avg = sum(intervals) / len(intervals)
            pace_status = "FAST" if avg < self.PACE_FAST else ("SLOW" if avg > self.PACE_SLOW else "MODERATE")

        rhythm_status = "N/A"
        if len(self._raise_times) >= 4:
            intervals = [
                self._raise_times[i] - self._raise_times[i - 1]
                for i in range(len(self._raise_times) - 3, len(self._raise_times))
            ]
            variance = max(intervals) - min(intervals)
            rhythm_status = "STEADY" if variance < 0.15 else ("IRREGULAR" if variance > 0.35 else "MODERATE")

        return {
            "reps":          self.reps,
            "pace_status":   pace_status,
            "knee_angle":    int(knee_angle),
            "rhythm_status": rhythm_status,
            "jump_status":   jump_status,
        }
