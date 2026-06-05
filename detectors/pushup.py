from core.base_excercise import BaseExcercise


class PushupDetector(BaseExcercise):
    """
    Tracks push-ups via elbow angle.
    Also monitors body alignment (shoulder-hip-ankle) and back arch (hip sag / pike).

    Landmarks used (MediaPipe Pose):
        11 LEFT_SHOULDER   12 RIGHT_SHOULDER
        13 LEFT_ELBOW      14 RIGHT_ELBOW
        15 LEFT_WRIST      16 RIGHT_WRIST
        23 LEFT_HIP        24 RIGHT_HIP
        27 LEFT_ANKLE      28 RIGHT_ANKLE
    """

    DOWN_THRESHOLD = 90   # elbow fully bent → bottom of push-up
    UP_THRESHOLD = 160    # elbow almost straight → top of push-up
    MIN_VISIBILITY = 0.6

    # Alignment thresholds (shoulder-hip-ankle angle)
    ALIGNMENT_GOOD_MIN = 160   # near 180° = flat plank
    ALIGNMENT_GOOD_MAX = 200
    # Back arch: hip y relative to shoulder-ankle line
    ARCH_THRESHOLD = 0.04      # fraction of image height

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx, elbow_idx, wrist_idx = self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST
            hip_idx, ankle_idx = self.LEFT_HIP, self.LEFT_ANKLE
        else:
            shoulder_idx, elbow_idx, wrist_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST
            hip_idx, ankle_idx = self.RIGHT_HIP, self.RIGHT_ANKLE

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        body_alignment_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
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

        # Body alignment status
        if self.ALIGNMENT_GOOD_MIN <= body_alignment_angle <= self.ALIGNMENT_GOOD_MAX:
            body_alignment = "STRAIGHT"
        elif body_alignment_angle < self.ALIGNMENT_GOOD_MIN:
            body_alignment = "PIKE (hips high)"
        else:
            body_alignment = "SAG (hips low)"

        # Hip position: compare hip y to the shoulder-ankle midpoint y
        hip_y = landmarks[hip_idx].y
        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        mid_y = (shoulder_y + ankle_y) / 2
        hip_diff = hip_y - mid_y

        if abs(hip_diff) <= self.ARCH_THRESHOLD:
            hip_status = "LEVEL"
        elif hip_diff < 0:
            hip_status = "HIPS TOO HIGH"
        else:
            hip_status = "HIPS TOO LOW"

        # Back arch: large deviation from straight
        if body_alignment_angle < 150:
            back_arch_status = "ARCHED"
        elif body_alignment_angle > 210:
            back_arch_status = "SAGGING"
        else:
            back_arch_status = "NEUTRAL"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "body_alignment": body_alignment,
            "hip_status": hip_status,
            "back_arch_status": back_arch_status,
        }