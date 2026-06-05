from core.base_excercise import BaseExcercise


class ShoulderPressDetector(BaseExcercise):
    """
    Rep logic  : elbow angle < DOWN_THRESHOLD → stage="down" (bar at shoulder height)
                 elbow angle >= UP_THRESHOLD  → stage="up"   + rep counted
    """

    DOWN_THRESHOLD = 90    # elbows bent, weight at shoulder level
    UP_THRESHOLD   = 155   # arms nearly fully extended overhead
    MIN_VISIBILITY = 0.65

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
            h_idx               = self.LEFT_HIP
        else:
            s_idx, e_idx, w_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST
            h_idx               = self.RIGHT_HIP

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
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if elbow_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # back arch: hip-shoulder alignment (lower-back shouldn't excessively arch)
        back_angle = self.calculate_angle(
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, e_idx),
        )
        back_arch_status = (
            "NEUTRAL" if back_angle >= 155
            else ("SLIGHT ARCH" if back_angle >= 135 else "EXCESSIVE ARCH")
        )

        # shoulder stability
        sh_diff = abs(landmarks[self.LEFT_SHOULDER].y - landmarks[self.RIGHT_SHOULDER].y)
        shoulder_status = "EVEN" if sh_diff < 0.05 else "UNEVEN"

        # extension at the top
        extension_status = "FULL" if elbow_angle >= self.UP_THRESHOLD else "PARTIAL"

        return {
            "reps":             self.reps,
            "elbow_angle":      int(elbow_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status,
            "shoulder_status":  shoulder_status,
        }