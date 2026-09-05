from core.base_excercise import BaseExcercise


class DipDetector(BaseExcercise):
    """
    Rep logic  : elbow angle < DOWN_THRESHOLD → stage="down"
                 elbow angle >= UP_THRESHOLD  → stage="up" + rep counted
    Shoulder depth: how far the shoulder dips below the elbow line.
    """

    DOWN_THRESHOLD = 80
    UP_THRESHOLD   = 155
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
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if elbow_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # shoulder depth: shoulder y vs elbow y
        # In MediaPipe, y increases downward; shoulder should descend below elbow at bottom
        sh_y = landmarks[s_idx].y
        e_y  = landmarks[e_idx].y
        depth_diff = sh_y - e_y   # positive when shoulder is below elbow

        if depth_diff > 0.04:
            shoulder_depth_status = "GOOD DEPTH"
        elif depth_diff > -0.02:
            shoulder_depth_status = "SHALLOW"
        else:
            shoulder_depth_status = "TOO HIGH"

        # body alignment (torso should be vertical → hip below shoulder)
        body_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, e_idx),
        )
        body_alignment = "GOOD" if body_angle >= 155 else ("SLIGHT LEAN" if body_angle >= 130 else "LEANING")

        # shoulder stability: both shoulders at similar height
        shoulder_diff = abs(landmarks[self.LEFT_SHOULDER].y - landmarks[self.RIGHT_SHOULDER].y)
        shoulder_status = "STABLE" if shoulder_diff < 0.05 else "UNEVEN"

        return {
            "reps":                 self.reps,
            "elbow_angle":          int(elbow_angle),
            "shoulder_depth_status": shoulder_depth_status,
            "body_alignment":       body_alignment,
            "shoulder_status":      shoulder_status,
        }