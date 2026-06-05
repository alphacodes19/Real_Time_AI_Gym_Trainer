from core.base_excercise import BaseExcercise


class PullupDetector(BaseExcercise):
    """
    Rep logic  : elbow angle >= DOWN_THRESHOLD → stage="down" (hanging)
                 elbow angle <= UP_THRESHOLD   → stage="up"   + rep counted
    Grip status inferred from wrist-shoulder width relative to shoulder width.
    """

    DOWN_THRESHOLD = 155   # arms straight, hanging
    UP_THRESHOLD   = 60    # chin above bar, elbows fully bent
    MIN_VISIBILITY = 0.60

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_ELBOW,     RIGHT_ELBOW     = 13, 14
    LEFT_WRIST,     RIGHT_WRIST     = 15, 16
    LEFT_HIP,       RIGHT_HIP       = 23, 24

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps  = 0
        self.stage = None

    def process(self, landmarks):
        if landmarks[self.LEFT_ELBOW].visibility >= landmarks[self.RIGHT_ELBOW].visibility:
            s_idx, e_idx, w_idx = self.LEFT_SHOULDER,  self.LEFT_ELBOW,  self.LEFT_WRIST
        else:
            s_idx, e_idx, w_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, e_idx),
            self.get_point(landmarks, w_idx),
        )

        key_visible = (
            landmarks[s_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[e_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[w_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_visible:
            if elbow_angle >= self.DOWN_THRESHOLD:
                self.stage = "down"
            if elbow_angle <= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # shoulder stability: both shoulders rising/dipping together
        sh_diff = abs(landmarks[self.LEFT_SHOULDER].y - landmarks[self.RIGHT_SHOULDER].y)
        shoulder_status = "STABLE" if sh_diff < 0.06 else "UNEVEN"

        # grip width: wrist span vs shoulder span
        wrist_span   = abs(landmarks[self.LEFT_WRIST].x - landmarks[self.RIGHT_WRIST].x)
        shoulder_span = abs(landmarks[self.LEFT_SHOULDER].x - landmarks[self.RIGHT_SHOULDER].x)
        ratio = wrist_span / max(shoulder_span, 0.01)
        if ratio < 0.9:
            grip_status = "NARROW GRIP"
        elif ratio <= 1.6:
            grip_status = "SHOULDER-WIDTH"
        else:
            grip_status = "WIDE GRIP"

        # full extension at the bottom
        extension_status = "FULL HANG" if elbow_angle >= self.DOWN_THRESHOLD else "PARTIAL"

        return {
            "reps":             self.reps,
            "elbow_angle":      int(elbow_angle),
            "shoulder_status":  shoulder_status,
            "grip_status":      grip_status,
            "extension_status": extension_status,
        }