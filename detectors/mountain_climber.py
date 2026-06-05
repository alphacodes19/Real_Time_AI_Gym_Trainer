from core.base_excercise import BaseExcercise
import time


class MountainClimberDetector(BaseExcercise):
    """
    Counts mountain climbers by tracking knee drive (knee y relative to hip y).
    Each time a knee rises above the hip (knee_y < hip_y) and returns = 1 drive.
    Two knee drives (left + right) = 1 rep.

    Metrics:
        pace_status    — drives per minute
        hip_status     — hips level and not bouncing
        body_alignment — plank position quality
        rhythm_status  — consistency of alternating knees
    """

    MIN_VISIBILITY = 0.5
    PACE_WINDOW = 5

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
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
        self._drives = 0          # each individual knee drive
        self._drive_times: list[float] = []

    def reset(self):
        self.reps = 0
        self.stage = None
        self._left_stage = None
        self._right_stage = None
        self._drives = 0
        self._drive_times = []

    def process(self, landmarks):
        left_hip_y = landmarks[self.LEFT_HIP].y
        right_hip_y = landmarks[self.RIGHT_HIP].y
        left_knee_y = landmarks[self.LEFT_KNEE].y
        right_knee_y = landmarks[self.RIGHT_KNEE].y

        # Knee drive: knee rises above hip line
        left_driven = left_knee_y < left_hip_y
        right_driven = right_knee_y < right_hip_y

        now = time.time()

        # Left knee
        if left_driven and self._left_stage != "up":
            self._left_stage = "up"
        elif not left_driven and self._left_stage == "up":
            self._left_stage = "down"
            self._drives += 1
            self._drive_times.append(now)

        # Right knee
        if right_driven and self._right_stage != "up":
            self._right_stage = "up"
        elif not right_driven and self._right_stage == "up":
            self._right_stage = "down"
            self._drives += 1
            self._drive_times.append(now)

        # 2 drives = 1 full rep
        self.reps = self._drives // 2

        # Pace (drives/min)
        self._drive_times = [t for t in self._drive_times if now - t <= self.PACE_WINDOW]
        dpm = len(self._drive_times) * (60 / self.PACE_WINDOW)
        if dpm == 0:
            pace_status = "RESTING"
        elif dpm < 20:
            pace_status = "SLOW"
        elif dpm <= 50:
            pace_status = "GOOD"
        else:
            pace_status = "FAST"

        # Hip level
        hip_diff = abs(left_hip_y - right_hip_y)
        hip_status = "LEVEL" if hip_diff < 0.05 else "BOUNCING"

        # Body alignment (plank) — shoulder-hip-ankle
        body_alignment_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_ANKLE),
        )
        if 155 <= body_alignment_angle <= 205:
            body_alignment = "STRAIGHT"
        elif body_alignment_angle < 155:
            body_alignment = "PIKE"
        else:
            body_alignment = "SAG"

        # Rhythm: alternating cadence consistency
        rhythm_status = "N/A"
        if len(self._drive_times) >= 4:
            intervals = [
                self._drive_times[i+1] - self._drive_times[i]
                for i in range(len(self._drive_times) - 1)
            ]
            avg = sum(intervals) / len(intervals)
            variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)
            rhythm_status = "STEADY" if variance < 0.05 else "UNSTEADY"

        return {
            "reps": self.reps,
            "pace_status": pace_status,
            "hip_status": hip_status,
            "body_alignment": body_alignment,
            "rhythm_status": rhythm_status,
        }