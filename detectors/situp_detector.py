from core.base_exercise import BaseExercise


class SitupDetector(BaseExercise):
    """
    Rep logic  : torso angle (shoulder-hip-knee) < DOWN_THRESHOLD → stage="down" (lying)
                 torso angle >= UP_THRESHOLD                       → stage="up" + rep counted
    """

    DOWN_THRESHOLD = 35    # torso nearly flat
    UP_THRESHOLD   = 75    # torso raised (past vertical mid-point)
    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_HIP,       RIGHT_HIP       = 23, 24
    LEFT_KNEE,      RIGHT_KNEE      = 25, 26
    LEFT_ANKLE,     RIGHT_ANKLE     = 27, 28
    NOSE = 0

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps  = 0
        self.stage = None

    def process(self, landmarks):
        if landmarks[self.LEFT_HIP].visibility >= landmarks[self.RIGHT_HIP].visibility:
            s_idx, h_idx, k_idx, a_idx = (
                self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE
            )
        else:
            s_idx, h_idx, k_idx, a_idx = (
                self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE
            )

        # torso angle: shoulder-hip-knee
        torso_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, k_idx),
        )
        # back angle: shoulder-hip-ankle (how flat the spine is)
        back_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, a_idx),
        )

        key_visible = (
            landmarks[s_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[h_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[k_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_visible:
            if torso_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if torso_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # ── form metrics ─────────────────────────────────────────────────────
        # hip flexor: knees should be bent (hip-knee-ankle angle)
        hip_knee_angle = self.calculate_angle(
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, k_idx),
            self.get_point(landmarks, a_idx),
        )
        hip_flexor_status = "GOOD" if hip_knee_angle < 100 else "OVEREXTENDED"

        # neck: proxy via nose y relative to shoulder y when torso is up
        nose_y    = landmarks[self.NOSE].y
        sh_y      = landmarks[s_idx].y
        neck_gap  = sh_y - nose_y          # positive = nose above shoulder
        if torso_angle >= self.UP_THRESHOLD:
            neck_status = "NEUTRAL" if neck_gap > 0.06 else "TUCKED"
        else:
            neck_status = "NEUTRAL"

        return {
            "reps":              self.reps,
            "torso_angle":       int(torso_angle),
            "hip_flexor_status": hip_flexor_status,
            "neck_status":       neck_status,
            "back_angle":        int(back_angle),
        }
