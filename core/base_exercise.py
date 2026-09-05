import math 
from abc import ABC, abstractmethod


class BaseExercise(ABC):
    def __init__(self):
        self.reps = 0
        self.stage = None

    def calculate_angle(self, a, b, c):
        ax, ay = a[0] - b[0], a[1] - b[1]
        cx, cy = c[0] - b[0], c[1] - b[1]

        dot = ax * cx + ay * cy

        mag_a = math.sqrt(ax ** 2 + ay ** 2)
        mag_c = math.sqrt(cx ** 2 + cy ** 2)

        if mag_a * mag_c == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))

        return math.degrees(math.acos(cos_angle))

    def get_point(self, landmarks, idx):
        p = landmarks[idx]

        return (p.x, p.y)

    def landmarks_visible(self, landmarks, *indices):
        """True only if every listed landmark is being tracked reliably.

        MediaPipe still returns coordinates for joints that are off-frame or
        occluded -- they're estimates, not observations. Counting reps from
        them produces phantom reps (e.g. a shoulder press 'counting' while
        the elbows and wrists are out of shot). Detectors should gate their
        rep logic on this.
        """
        threshold = getattr(self, "MIN_VISIBILITY", 0.6)

        for idx in indices:
            if landmarks[idx].visibility < threshold:
                return False

        return True

    @abstractmethod
    def process(self, landmarks):
        pass

    @abstractmethod
    def reset(self):
        pass
