from core.base_excercise import BaseExcercise


class BenchPressDetector(BaseExcercise):
    """
    Rep logic  : elbow angle < DOWN_THRESHOLD → stage="down" (bar near chest)
                 elbow angle >= UP_THRESHOLD  → stage="up"   + rep counted
    Assumes user is lying on a bench and camera sees them from the side.
    """

    DOWN_THRESHOLD = 75    # elbows bent, bar near chest
    UP_THRESHOLD   = 155   # arms extended
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

        # back arch: hip lifted off bench is a form fault
        # when lying down, hip y should be close to shoulder y (both horizontal)
        sh_y = landmarks[s_idx].y
        h_y  = landmarks[h_idx].y
        y_diff = abs(sh_y - h_y)
        back_arch_status = "NEUTRAL" if y_diff < 0.12 else ("SLIGHT ARCH" if y_diff < 0.20 else "EXCESSIVE ARCH")

        # shoulder stability
        sh_diff = abs(landmarks[self.LEFT_SHOULDER].y - landmarks[self.RIGHT_SHOULDER].y)
        shoulder_status = "STABLE" if sh_diff < 0.05 else "UNEVEN"

        # extension
        extension_status = "FULL LOCKOUT" if elbow_angle >= self.UP_THRESHOLD else "PARTIAL"

        return {
            "reps":             self.reps,
            "elbow_angle":      int(elbow_angle),
            "back_arch_status": back_arch_status,
            "shoulder_status":  shoulder_status,
            "extension_status": extension_status,
        }