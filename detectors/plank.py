from core.base_excercise import BaseExcercise
import time


class PlankDetector(BaseExcercise):
    """
    Planks are a hold, not a rep movement.
    Counts a "rep" (hold) each time the user maintains plank position for
    HOLD_SECONDS continuously, then breaks position.

    Monitors:
        back_angle     shoulder-hip-ankle straightness
        hip_status     hips level
        body_alignment overall straight-line quality
        hip_drop       hips sagging below shoulder-ankle line
    """

    HOLD_SECONDS = 5          # seconds of good form = 1 completed hold
    BACK_STRAIGHT_MIN = 160   # shoulder-hip-ankle angle range for good plank
    BACK_STRAIGHT_MAX = 200
    HIP_DROP_THRESHOLD = 0.04 # fraction of frame height
    MIN_VISIBILITY = 0.6

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self._hold_start: float | None = None

    def reset(self):
        self.reps = 0
        self.stage = None
        self._hold_start = None

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_SHOULDER].visibility
        right_vis = landmarks[self.RIGHT_SHOULDER].visibility

        if left_vis >= right_vis:
            shoulder_idx, hip_idx, ankle_idx = self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_ANKLE
        else:
            shoulder_idx, hip_idx, ankle_idx = self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_ANKLE

        back_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        # Hip level: compare both hips
        hip_left_y = landmarks[self.LEFT_HIP].y
        hip_right_y = landmarks[self.RIGHT_HIP].y
        hip_status = "LEVEL" if abs(hip_left_y - hip_right_y) < 0.04 else "TILTED"

        # Body alignment (same angle)
        if self.BACK_STRAIGHT_MIN <= back_angle <= self.BACK_STRAIGHT_MAX:
            body_alignment = "STRAIGHT"
        elif back_angle < self.BACK_STRAIGHT_MIN:
            body_alignment = "PIKE"
        else:
            body_alignment = "SAG"

        # Hip drop: hip y vs midpoint of shoulder-ankle
        hip_y = landmarks[hip_idx].y
        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        mid_y = (shoulder_y + ankle_y) / 2
        hip_drop_status = "DROPPING" if (hip_y - mid_y) > self.HIP_DROP_THRESHOLD else "GOOD"

        in_good_plank = (
            body_alignment == "STRAIGHT"
            and hip_drop_status == "GOOD"
            and landmarks[hip_idx].visibility >= self.MIN_VISIBILITY
        )

        now = time.time()
        if in_good_plank:
            if self._hold_start is None:
                self._hold_start = now
            elif now - self._hold_start >= self.HOLD_SECONDS:
                self.reps += 1
                self._hold_start = None   # reset so next hold counts separately
        else:
            self._hold_start = None

        return {
            "reps": self.reps,          # number of completed holds
            "back_angle": int(back_angle),
            "hip_status": hip_status,
            "body_alignment": body_alignment,
            "hip_drop_status": hip_drop_status,
        }