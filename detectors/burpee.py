from core.base_excercise import BaseExcercise
import time


class BurpeeDetector(BaseExcercise):
    """
    Burpee phase detection using hip height as a proxy:
        STANDING  → HIP_HIGH
        PLANK     → HIP_LOW  (hip y close to shoulder y, both high in frame)
        JUMP      → HIP_RISING (hip y drops quickly)

    Phase cycle: STANDING → PLANK → STANDING (with jump) = 1 rep.

    Metrics:
        phase          — current movement phase
        jump_status    — detected jump at the top
        pace_status    — reps per minute
        body_alignment — shoulder-hip-ankle during plank phase
    """

    MIN_VISIBILITY = 0.5
    PACE_WINDOW = 10

    # Normalised y thresholds (0=top, 1=bottom of frame)
    HIP_STANDING_Y = 0.55   # hip y when standing (rough centre of frame)
    HIP_PLANK_Y = 0.40      # hip y when in plank (higher = lower number)

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def __init__(self):
        super().__init__()
        self._rep_times: list[float] = []
        self._prev_hip_y: float | None = None

    def reset(self):
        self.reps = 0
        self.stage = None
        self._rep_times = []
        self._prev_hip_y = None

    def process(self, landmarks):
        avg_hip_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2
        avg_shoulder_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2

        # Phase detection
        if avg_hip_y > self.HIP_STANDING_Y:
            phase = "STANDING"
        elif avg_hip_y < self.HIP_PLANK_Y:
            phase = "PLANK"
        else:
            phase = "TRANSITIONING"

        # Rep count: PLANK → STANDING transition
        if self.stage == "plank" and phase == "STANDING":
            self.stage = "standing"
            self.reps += 1
            self._rep_times.append(time.time())
        elif phase == "PLANK":
            self.stage = "plank"
        elif phase == "STANDING" and self.stage is None:
            self.stage = "standing"

        # Jump detection: hip y dropping fast (moving up in image)
        jump_status = "N/A"
        if self._prev_hip_y is not None:
            delta = self._prev_hip_y - avg_hip_y
            jump_status = "JUMPING" if delta > 0.015 else "GROUNDED"
        self._prev_hip_y = avg_hip_y

        # Pace
        now = time.time()
        self._rep_times = [t for t in self._rep_times if now - t <= self.PACE_WINDOW]
        rpm = len(self._rep_times) * (60 / self.PACE_WINDOW)
        if rpm == 0:
            pace_status = "RESTING"
        elif rpm < 8:
            pace_status = "SLOW"
        elif rpm <= 15:
            pace_status = "GOOD"
        else:
            pace_status = "FAST"

        # Body alignment during plank
        body_alignment_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_ANKLE),
        )
        if 160 <= body_alignment_angle <= 200:
            body_alignment = "STRAIGHT"
        elif body_alignment_angle < 160:
            body_alignment = "PIKE"
        else:
            body_alignment = "SAG"

        return {
            "reps": self.reps,
            "phase": phase,
            "jump_status": jump_status,
            "pace_status": pace_status,
            "body_alignment": body_alignment,
        }