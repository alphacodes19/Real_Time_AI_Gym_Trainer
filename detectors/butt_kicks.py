from core.base_excercise import BaseExcercise
import time


class ButtKickDetector(BaseExcercise):
    """
    Counts butt kicks by tracking heel (ankle) rising toward the hip.
    Each ankle-to-hip approach (ankle_y < knee_y * factor) = 1 kick.
    2 kicks = 1 rep.

    Metrics:
        pace_status   — kicks per minute
        knee_angle    — hip-knee-ankle of the kicking leg (should be very acute)
        rhythm_status — consistency
        swing_status  — whether the heel actually reaches the glutes
    """

    MIN_VISIBILITY = 0.5
    PACE_WINDOW = 5
    # Heel-to-glute: ankle y should approach hip y from below
    # knee_angle < 60° indicates a proper kick
    KICK_ANGLE_THRESHOLD = 70

    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self._left_stage = None
        self._right_stage = None
        self._kicks = 0
        self._kick_times: list[float] = []

    def reset(self):
        self.reps = 0
        self.stage = None
        self._left_stage = None
        self._right_stage = None
        self._kicks = 0
        self._kick_times = []

    def _knee_angle(self, landmarks, hip_idx, knee_idx, ankle_idx):
        return self.calculate_angle(
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
            self.get_point(landmarks, ankle_idx),
        )

    def process(self, landmarks):
        now = time.time()

        left_angle = self._knee_angle(landmarks, self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE)
        right_angle = self._knee_angle(landmarks, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE)

        left_kicked = left_angle < self.KICK_ANGLE_THRESHOLD
        right_kicked = right_angle < self.KICK_ANGLE_THRESHOLD

        # Left kick
        if left_kicked and self._left_stage != "kicked":
            self._left_stage = "kicked"
        elif not left_kicked and self._left_stage == "kicked":
            self._left_stage = "resting"
            self._kicks += 1
            self._kick_times.append(now)

        # Right kick
        if right_kicked and self._right_stage != "kicked":
            self._right_stage = "kicked"
        elif not right_kicked and self._right_stage == "kicked":
            self._right_stage = "resting"
            self._kicks += 1
            self._kick_times.append(now)

        self.reps = self._kicks // 2

        # Report angle of the active kicking leg
        if left_kicked:
            knee_angle = left_angle
        elif right_kicked:
            knee_angle = right_angle
        else:
            knee_angle = min(left_angle, right_angle)

        # Pace
        self._kick_times = [t for t in self._kick_times if now - t <= self.PACE_WINDOW]
        kpm = len(self._kick_times) * (60 / self.PACE_WINDOW)
        if kpm == 0:
            pace_status = "RESTING"
        elif kpm < 20:
            pace_status = "SLOW"
        elif kpm <= 60:
            pace_status = "GOOD"
        else:
            pace_status = "FAST"

        # Swing: is the heel reaching high enough?
        swing_status = "GOOD KICK" if (left_kicked or right_kicked) else "KICK HIGHER"

        # Rhythm
        rhythm_status = "N/A"
        if len(self._kick_times) >= 4:
            intervals = [
                self._kick_times[i+1] - self._kick_times[i]
                for i in range(len(self._kick_times) - 1)
            ]
            avg = sum(intervals) / len(intervals)
            variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)
            rhythm_status = "STEADY" if variance < 0.05 else "UNSTEADY"

        return {
            "reps": self.reps,
            "knee_angle": int(knee_angle),
            "pace_status": pace_status,
            "rhythm_status": rhythm_status,
            "swing_status": swing_status,
        }