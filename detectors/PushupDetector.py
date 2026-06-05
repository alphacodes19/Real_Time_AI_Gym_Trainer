from core.base_excercise import BaseExcercise


class PushupDetector(BaseExcercise):
    """
    Rep logic  : elbow angle < DOWN_THRESHOLD  → stage="down"
                 elbow angle >= UP_THRESHOLD   → stage="up"  + rep counted
    Side chosen: whichever elbow landmark has higher MediaPipe visibility score.
    """

    DOWN_THRESHOLD = 90    # elbow nearly bent (chest near floor)
    UP_THRESHOLD   = 155   # elbow mostly extended (arms straight)
    MIN_VISIBILITY = 0.7

    # MediaPipe landmark indices
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_ELBOW,    RIGHT_ELBOW    = 13, 14
    LEFT_WRIST,    RIGHT_WRIST    = 15, 16
    LEFT_HIP,      RIGHT_HIP      = 23, 24
    LEFT_ANKLE,    RIGHT_ANKLE    = 27, 28

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps  = 0
        self.stage = None

    def process(self, landmarks):
        # ── pick the more-visible side ──────────────────────────────────────
        if landmarks[self.LEFT_ELBOW].visibility >= landmarks[self.RIGHT_ELBOW].visibility:
            s_idx, e_idx, w_idx = self.LEFT_SHOULDER,  self.LEFT_ELBOW,  self.LEFT_WRIST
            h_idx, a_idx        = self.LEFT_HIP,        self.LEFT_ANKLE
            opp_h_idx           = self.RIGHT_HIP
        else:
            s_idx, e_idx, w_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST
            h_idx, a_idx        = self.RIGHT_HIP,       self.RIGHT_ANKLE
            opp_h_idx           = self.LEFT_HIP

        # ── angles ──────────────────────────────────────────────────────────
        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, e_idx),
            self.get_point(landmarks, w_idx),
        )
        # shoulder → hip → ankle: measures straightness of the body plank
        body_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, a_idx),
        )

        # ── rep counting ─────────────────────────────────────────────────────
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

        # ── form metrics ─────────────────────────────────────────────────────
        if body_angle >= 165:
            body_alignment = "GOOD"
        elif body_angle >= 145:
            body_alignment = "SLIGHT BEND"
        else:
            body_alignment = "POOR"

        hip_y      = landmarks[h_idx].y
        shoulder_y = landmarks[s_idx].y
        ankle_y    = landmarks[a_idx].y
        mid_y      = (shoulder_y + ankle_y) / 2
        if hip_y < mid_y - 0.05:
            back_arch_status = "HIPS HIGH"
        elif hip_y > mid_y + 0.05:
            back_arch_status = "HIPS LOW"
        else:
            back_arch_status = "NEUTRAL"

        hip_status = (
            "LEVEL"
            if abs(landmarks[self.LEFT_HIP].y - landmarks[self.RIGHT_HIP].y) < 0.04
            else "TILTED"
        )

        return {
            "reps":             self.reps,
            "elbow_angle":      int(elbow_angle),
            "body_alignment":   body_alignment,
            "hip_status":       hip_status,
            "back_arch_status": back_arch_status,
        }