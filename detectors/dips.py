from core.base_excercise import BaseExcercise


class DipDetector(BaseExcercise):
    """
    Tracks dips via elbow angle (shoulder-elbow-wrist).
    Also monitors shoulder depth (shoulder dropping below elbow line)
    and body alignment (torso vertical).

    Landmarks:
        11/12 SHOULDER  13/14 ELBOW  15/16 WRIST  23/24 HIP
    """

    DOWN_THRESHOLD = 90    # elbow fully bent
    UP_THRESHOLD = 160     # arms almost fully extended
    MIN_VISIBILITY = 0.6

    SHOULDER_DEPTH_THRESHOLD = 0.02   # shoulder y vs elbow y (norm coords)

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx, elbow_idx, wrist_idx, hip_idx = (
                self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST, self.LEFT_HIP
            )
        else:
            shoulder_idx, elbow_idx, wrist_idx, hip_idx = (
                self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST, self.RIGHT_HIP
            )

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        key_visible = (
            landmarks[shoulder_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[elbow_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[wrist_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_visible:
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if elbow_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Shoulder depth: shoulder should dip level with or below elbow
        shoulder_y = landmarks[shoulder_idx].y
        elbow_y = landmarks[elbow_idx].y
        # In image coords y increases downward; shoulder dipping = shoulder_y > elbow_y
        depth_diff = shoulder_y - elbow_y
        if depth_diff >= -self.SHOULDER_DEPTH_THRESHOLD:
            shoulder_depth_status = "GOOD DEPTH"
        else:
            shoulder_depth_status = "TOO SHALLOW"

        # Body alignment: shoulder-hip should be roughly vertical (x close)
        shoulder_x = landmarks[shoulder_idx].x
        hip_x = landmarks[hip_idx].x
        body_alignment = "STRAIGHT" if abs(shoulder_x - hip_x) < 0.08 else "LEANING"

        # Shoulder status: are shoulders protracted/shrugged (shoulder y vs elbow y at top)
        if self.stage == "up":
            shoulder_status = "DEPRESSED" if shoulder_y < elbow_y else "SHRUGGED"
        else:
            shoulder_status = "N/A"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_depth_status": shoulder_depth_status,
            "body_alignment": body_alignment,
            "shoulder_status": shoulder_status,
        }