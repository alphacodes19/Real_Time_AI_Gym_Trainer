from core.base_excercise import BaseExcercise


class LungeDetector(BaseExcercise):
    """
    Rep logic  : front knee angle < DOWN_THRESHOLD → stage="down"
                 front knee angle >= UP_THRESHOLD  → stage="up" + rep counted
    Front leg  : whichever knee has a smaller (more bent) angle at a given frame,
                 or the more-visible one when standing.
    """

    DOWN_THRESHOLD = 100   # deep lunge
    UP_THRESHOLD   = 160   # standing
    MIN_VISIBILITY = 0.65

    LEFT_HIP,      RIGHT_HIP      = 23, 24
    LEFT_KNEE,     RIGHT_KNEE     = 25, 26
    LEFT_ANKLE,    RIGHT_ANKLE    = 27, 28
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps  = 0
        self.stage = None

    def process(self, landmarks):
        # ── per-side knee angles ─────────────────────────────────────────────
        left_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
            self.get_point(landmarks, self.LEFT_ANKLE),
        )
        right_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
            self.get_point(landmarks, self.RIGHT_ANKLE),
        )

        # front leg = more-bent knee
        if left_knee_angle <= right_knee_angle:
            front_knee_angle = left_knee_angle
            h_idx, k_idx, a_idx  = self.LEFT_HIP,  self.LEFT_KNEE,  self.LEFT_ANKLE
            sh_idx               = self.LEFT_SHOULDER
        else:
            front_knee_angle = right_knee_angle
            h_idx, k_idx, a_idx  = self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE
            sh_idx               = self.RIGHT_SHOULDER

        # torso uprightness: shoulder → hip → knee
        torso_angle = self.calculate_angle(
            self.get_point(landmarks, sh_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, k_idx),
        )

        # ── rep counting ─────────────────────────────────────────────────────
        key_visible = (
            landmarks[h_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[k_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[a_idx].visibility >= self.MIN_VISIBILITY
        )
        if key_visible:
            if front_knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if front_knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # ── form metrics ─────────────────────────────────────────────────────
        if torso_angle >= 160:
            torso_status = "UPRIGHT"
        elif torso_angle >= 140:
            torso_status = "SLIGHT LEAN"
        else:
            torso_status = "EXCESSIVE LEAN"

        # hip level
        hip_diff = abs(landmarks[self.LEFT_HIP].y - landmarks[self.RIGHT_HIP].y)
        hip_status = "LEVEL" if hip_diff < 0.05 else "TILTED"

        # lateral balance via shoulder level
        shoulder_diff = abs(landmarks[self.LEFT_SHOULDER].x - landmarks[self.RIGHT_SHOULDER].x)
        balance_status = "STABLE" if shoulder_diff > 0.15 else "NARROW"

        return {
            "reps":             self.reps,
            "front_knee_angle": int(front_knee_angle),
            "torso_angle":      int(torso_angle),
            "balance_status":   balance_status,
            "hip_status":       hip_status,
        }