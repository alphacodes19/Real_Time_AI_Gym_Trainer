from core.base_excercise import BaseExcercise
import time


class JumpingJackDetector(BaseExcercise):
    """
    Counts jumping jacks by tracking wrist height relative to shoulder height.
    Arms-up (wrists above shoulders) → arms-down (wrists below hips) = 1 rep.

    Also reports:
        jump_status   — are both feet off ground? (approximate: hip y rising)
        rhythm_status — consistent cadence
        pace_status   — reps per minute
    """

    MIN_VISIBILITY = 0.5
    PACE_WINDOW = 5          # seconds to compute rolling pace

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_WRIST = 15
    RIGHT_WRIST = 16

    def __init__(self):
        super().__init__()
        self._rep_times: list[float] = []
        self._prev_hip_y: float | None = None
        self._jump_frames = 0

    def reset(self):
        self.reps = 0
        self.stage = None
        self._rep_times = []
        self._prev_hip_y = None
        self._jump_frames = 0

    def process(self, landmarks):
        left_wrist_y = landmarks[self.LEFT_WRIST].y
        right_wrist_y = landmarks[self.RIGHT_WRIST].y
        left_shoulder_y = landmarks[self.LEFT_SHOULDER].y
        right_shoulder_y = landmarks[self.RIGHT_SHOULDER].y
        left_hip_y = landmarks[self.LEFT_HIP].y
        right_hip_y = landmarks[self.RIGHT_HIP].y

        avg_wrist_y = (left_wrist_y + right_wrist_y) / 2
        avg_shoulder_y = (left_shoulder_y + right_shoulder_y) / 2
        avg_hip_y = (left_hip_y + right_hip_y) / 2

        # MediaPipe y=0 is top of frame; smaller y = higher in frame
        arms_up = avg_wrist_y < avg_shoulder_y       # wrists above shoulders
        arms_down = avg_wrist_y > avg_hip_y           # wrists below hips

        if arms_up:
            self.stage = "up"
        if arms_down and self.stage == "up":
            self.stage = "down"
            self.reps += 1
            self._rep_times.append(time.time())

        # Jump detection: hip y decreasing (moving up) significantly
        jump_status = "N/A"
        if self._prev_hip_y is not None:
            delta = self._prev_hip_y - avg_hip_y   # positive = moved up
            jump_status = "JUMPING" if delta > 0.01 else "GROUNDED"
        self._prev_hip_y = avg_hip_y

        # Pace (reps/min) over last PACE_WINDOW seconds
        now = time.time()
        self._rep_times = [t for t in self._rep_times if now - t <= self.PACE_WINDOW]
        reps_in_window = len(self._rep_times)
        rpm = reps_in_window * (60 / self.PACE_WINDOW)
        if rpm == 0:
            pace_status = "RESTING"
        elif rpm < 30:
            pace_status = "SLOW"
        elif rpm <= 60:
            pace_status = "GOOD"
        else:
            pace_status = "FAST"

        # Rhythm: are rep intervals consistent?
        rhythm_status = "N/A"
        if len(self._rep_times) >= 3:
            intervals = [self._rep_times[i+1] - self._rep_times[i] for i in range(len(self._rep_times)-1)]
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval)**2 for x in intervals) / len(intervals)
            rhythm_status = "STEADY" if variance < 0.08 else "UNSTEADY"

        return {
            "reps": self.reps,
            "jump_status": jump_status,
            "pace_status": pace_status,
            "rhythm_status": rhythm_status,
        }