from core.base_excercise import BaseExcercise


class BicepCurlDetector(BaseExcercise):
    """
    Rep logic  : elbow angle >= DOWN_THRESHOLD → stage="down" (arm extended)
                 elbow angle <= UP_THRESHOLD   → stage="up"   + rep counted
    Swing detection: shoulder y movement between frames.
    """

    DOWN_THRESHOLD = 155   # arm extended
    UP_THRESHOLD   = 50    # arm fully curled
    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_ELBOW,     RIGHT_ELBOW     = 13, 14
    LEFT_WRIST,     RIGHT_WRIST     = 15, 16
    LEFT_HIP,       RIGHT_HIP       = 23, 24

    def __init__(self):
        super().__init__()
        self._prev_shoulder_y = None
        self._swing_buffer    = []

    def reset(self):
        self.reps              = 0
        self.stage             = None
        self._prev_shoulder_y  = None
        self._swing_buffer     = []

    def process(self, landmarks):
        if landmarks[self.LEFT_ELBOW].visibility >= landmarks[self.RIGHT_ELBOW].visibility:
            s_idx, e_idx, w_idx = self.LEFT_SHOULDER,  self.LEFT_ELBOW,  self.LEFT_WRIST
            h_idx               = self.LEFT_HIP
            opp_s               = self.RIGHT_SHOULDER
        else:
            s_idx, e_idx, w_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST
            h_idx               = self.RIGHT_HIP
            opp_s               = self.LEFT_SHOULDER

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

        # ── swing detection (shoulder moving up/down excessively) ────────────
        cur_sh_y = landmarks[s_idx].y
        if self._prev_shoulder_y is not None:
            delta = abs(cur_sh_y - self._prev_shoulder_y)
            self._swing_buffer.append(delta)
            if len(self._swing_buffer) > 10:
                self._swing_buffer.pop(0)
        self._prev_shoulder_y = cur_sh_y

        avg_swing = sum(self._swing_buffer) / len(self._swing_buffer) if self._swing_buffer else 0
        swing_status = "SWINGING" if avg_swing > 0.015 else "CONTROLLED"

        # shoulder stability: shoulder y relative to hip y (should stay constant)
        sh_hip_diff = abs(landmarks[s_idx].y - landmarks[h_idx].y)
        shoulder_status = "STABLE" if sh_hip_diff > 0.2 else "RAISED"

        # extension: arm fully extended at bottom
        extension_status = "FULL EXTENSION" if elbow_angle >= self.DOWN_THRESHOLD else "PARTIAL"

        return {
            "reps":             self.reps,
            "elbow_angle":      int(elbow_angle),
            "shoulder_status":  shoulder_status,
            "swing_status":     swing_status,
            "extension_status": extension_status,
        }