from core.base_exercise import BaseExercise


class DeadliftDetector(BaseExercise):
    """
    Rep logic  : hip angle (shoulder-hip-knee) < DOWN_THRESHOLD → stage="down" (hinging)
                 hip angle >= UP_THRESHOLD                       → stage="up"  + rep counted
    """

    DOWN_THRESHOLD = 120   # deep hip hinge
    UP_THRESHOLD   = 165   # standing tall
    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER,  RIGHT_SHOULDER  = 11, 12
    LEFT_HIP,       RIGHT_HIP       = 23, 24
    LEFT_KNEE,      RIGHT_KNEE      = 25, 26
    LEFT_ANKLE,     RIGHT_ANKLE     = 27, 28

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
            opp_h = self.RIGHT_HIP
        else:
            s_idx, h_idx, k_idx, a_idx = (
                self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE
            )
            opp_h = self.LEFT_HIP

        # hip angle: shoulder-hip-knee (how much hip hinge)
        hip_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, k_idx),
        )
        # knee angle
        knee_angle = self.calculate_angle(
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, k_idx),
            self.get_point(landmarks, a_idx),
        )
        # back angle: shoulder-hip-ankle (spine neutrality)
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
            if hip_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if hip_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # back roundness
        if back_angle >= 160:
            body_alignment = "NEUTRAL SPINE"
        elif back_angle >= 140:
            body_alignment = "SLIGHT ROUND"
        else:
            body_alignment = "ROUNDED BACK"

        hip_status = (
            "LEVEL" if abs(landmarks[self.LEFT_HIP].y - landmarks[opp_h].y) < 0.04
            else "TILTED"
        )

        return {
            "reps":           self.reps,
            "knee_angle":     int(knee_angle),
            "back_angle":     int(back_angle),
            "hip_status":     hip_status,
            "body_alignment": body_alignment,
        }
