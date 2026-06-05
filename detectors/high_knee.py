from core.base_excercise import BaseExcercise
import time


class HighKneeDetector(BaseExcercise):
    """
    Counts high knees by detecting each knee crossing above the hip.
    Each individual knee raise = 1 drive; 2 drives = 1 rep.

    Metrics:
        pace_status   — drives per minute
        knee_angle    — hip-knee-ankle of the raised leg
        rhythm_status — cadence consistency
        jump_status   — whether feet are leaving the ground
    """

    MIN_VISIBILITY = 0.5
    PACE_WINDOW = 5
    KNEE_HEIGHT_THRESHOLD = 0.02   # how far knee_y must be above hip_y

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
        self._drives = 0
        self._drive_times: list[float] = []
        self._prev_avg_hip_y: float | None = None

    def reset(self):
        self.reps = 0
        self.stage = None
        self._left_stage = None
        self._right_stage = None
        self._drives = 0
        self._drive_times = []
        self._prev_avg_hip_y = None

    def process(self, landmarks):
        now = time.time()

        left_hip_y = landmarks[self.LEFT_HIP].y
        right_hip_y = landmarks[self.RIGHT_HIP].y
        left_knee_y = landmarks[self.LEFT_KNEE].y
        right_knee_y = landmarks[self.RIGHT_KNEE].y

        left_raised = (left_hip_y - left_knee_y) > self.KNEE_HEIGHT_THRESHOLD
        right_raised = (right_hip_y - right_knee_y) > self.KNEE_HEIGHT_THRESHOLD

        # Left knee drive
        if left_raised and self._left_stage != "up":
            self._left_stage = "up"
        elif not left_raised and self._left_stage == "up":
            self._left_stage = "down"
            self._drives += 1
            self._drive_times.append(now)

        # Right knee drive
        if right_raised and self._right_stage != "up":
            self._right_stage = "up"
        elif not right_raised and self._right_stage == "up":
            self._right_stage = "down"
            self._drives += 1
            self._drive_times.append(now)

        self.reps = self._drives // 2

        # Knee angle of the currently raised knee
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

        # Pace
        self._drive_times = [t for t in self._drive_times if now - t <= self.PACE_WINDOW]
        dpm = len(self._drive_times) * (60 / self.PACE_WINDOW)
        if dpm == 0:
            pace_status = "RESTING"
        elif dpm < 20:
            pace_status = "SLOW"
        elif dpm <= 60:
            pace_status = "GOOD"
        else:
            pace_status = "FAST"

        # Rhythm
        rhythm_status = "N/A"
        if len(self._drive_times) >= 4:
            intervals = [
                self._drive_times[i+1] - self._drive_times[i]
                for i in range(len(self._drive_times) - 1)
            ]
            avg = sum(intervals) / len(intervals)
            variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)
            rhythm_status = "STEADY" if variance < 0.05 else "UNSTEADY"

        # Jump: hips rising
        avg_hip_y = (left_hip_y + right_hip_y) / 2
        jump_status = "N/A"
        if self._prev_avg_hip_y is not None:
            delta = self._prev_avg_hip_y - avg_hip_y
            jump_status = "JUMPING" if delta > 0.01 else "GROUNDED"
        self._prev_avg_hip_y = avg_hip_y

        return {
            "reps": self.reps,
            "knee_angle": int(knee_angle),
            "pace_status": pace_status,
            "rhythm_status": rhythm_status,
            "jump_status": jump_status,
        }