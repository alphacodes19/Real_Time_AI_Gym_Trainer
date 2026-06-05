from core.base_excercise import BaseExcercise


class LungeDetector(BaseExcercise):
    """
    Tracks lunges via the front-knee angle (hip-knee-ankle on the leading leg).
    Automatically picks the more-bent knee as the front leg each frame.

    Landmarks:
        23 LEFT_HIP    24 RIGHT_HIP
        25 LEFT_KNEE   26 RIGHT_KNEE
        27 LEFT_ANKLE  28 RIGHT_ANKLE
        11 LEFT_SHOULDER / 12 RIGHT_SHOULDER  (torso angle)
    """

    DOWN_THRESHOLD = 100   # front knee bent ≤ 100° → lunge depth reached
    UP_THRESHOLD = 160     # front knee extended → standing
    MIN_VISIBILITY = 0.6

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
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

        # The front leg is the more-bent one
        if left_knee_angle <= right_knee_angle:
            front_knee_angle = left_knee_angle
            hip_idx, knee_idx, ankle_idx = self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE
            shoulder_idx = self.LEFT_SHOULDER
        else:
            front_knee_angle = right_knee_angle
            hip_idx, knee_idx, ankle_idx = self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE
            shoulder_idx = self.RIGHT_SHOULDER

        # Torso upright angle: shoulder-hip-knee
        torso_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        key_visible = (
            landmarks[hip_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[knee_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[ankle_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_visible:
            if front_knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if front_knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Balance: compare left/right hip y
        hip_left_y = landmarks[self.LEFT_HIP].y
        hip_right_y = landmarks[self.RIGHT_HIP].y
        hip_diff = abs(hip_left_y - hip_right_y)
        balance_status = "BALANCED" if hip_diff < 0.05 else "UNBALANCED"

        # Hip status: are hips level enough?
        hip_status = "LEVEL" if hip_diff < 0.05 else "TILTED"

        return {
            "reps": self.reps,
            "front_knee_angle": int(front_knee_angle),
            "torso_angle": int(torso_angle),
            "balance_status": balance_status,
            "hip_status": hip_status,
        }