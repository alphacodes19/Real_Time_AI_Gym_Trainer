import time
from core.base_exercise import BaseExercise


class ButtKickDetector(BaseExercise):
    """
    Rep logic  : heel drawn up toward glute → knee angle becomes small
                 Knee (hip-knee-ankle) angle < KICK_THRESHOLD → kick detected.
                 Alternating per leg; each kick = 0.5 rep.
    """

    KICK_THRESHOLD  = 75    # knee angle when heel is near glute
    RESET_THRESHOLD = 145   # knee angle when leg is extended again
    MIN_VISIBILITY  = 0.55
    PACE_FAST = 0.4
    PACE_SLOW = 1.0

    LEFT_HIP,   RIGHT_HIP   = 23, 24
    LEFT_KNEE,  RIGHT_KNEE  = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28

    def __init__(self):
        super().__init__()
        self._half_reps   = 0
        self._left_state  = "extended"
        self._right_state = "extended"
        self._kick_times: list[float] = []

    def reset(self):
        self.reps          = 0
        self.stage         = None
        self._half_reps    = 0
        self._left_state   = "extended"
        self._right_state  = "extended"
        self._kick_times   = []

    def process(self, landmarks):
        left_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
            self.get_point(landmarks, self.LEFT_ANKLE),
        )
        right_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
            self.get_point(landmarks, self.RIGHT_ANKLE),
        )

        # left kick
        if left_knee_angle < self.KICK_THRESHOLD and self._left_state == "extended":
            self._left_state = "kicked"
            self._half_reps += 1
            self._kick_times.append(time.time())
        elif left_knee_angle >= self.RESET_THRESHOLD and self._left_state == "kicked":
            self._left_state = "extended"

        # right kick
        if right_knee_angle < self.KICK_THRESHOLD and self._right_state == "extended":
            self._right_state = "kicked"
            self._half_reps += 1
            self._kick_times.append(time.time())
        elif right_knee_angle >= self.RESET_THRESHOLD and self._right_state == "kicked":
            self._right_state = "extended"

        self.reps  = self._half_reps // 2
        self.stage = "active"

        # report the more-bent knee angle
        knee_angle = min(left_knee_angle, right_knee_angle)

        swing_status = (
            "KICKING" if (left_knee_angle < self.KICK_THRESHOLD or
                          right_knee_angle < self.KICK_THRESHOLD)
            else "RUNNING"
        )

        pace_status = "N/A"
        if len(self._kick_times) >= 2:
            n = min(len(self._kick_times), 6)
            intervals = [
                self._kick_times[i] - self._kick_times[i - 1]
                for i in range(len(self._kick_times) - n + 1, len(self._kick_times))
            ]
            avg = sum(intervals) / len(intervals)
            pace_status = "FAST" if avg < self.PACE_FAST else ("SLOW" if avg > self.PACE_SLOW else "MODERATE")

        rhythm_status = "N/A"
        if len(self._kick_times) >= 4:
            intervals = [
                self._kick_times[i] - self._kick_times[i - 1]
                for i in range(len(self._kick_times) - 3, len(self._kick_times))
            ]
            variance = max(intervals) - min(intervals)
            rhythm_status = "STEADY" if variance < 0.15 else ("IRREGULAR" if variance > 0.35 else "MODERATE")

        return {
            "reps":          self.reps,
            "pace_status":   pace_status,
            "knee_angle":    int(knee_angle),
            "rhythm_status": rhythm_status,
            "swing_status":  swing_status,
        }
