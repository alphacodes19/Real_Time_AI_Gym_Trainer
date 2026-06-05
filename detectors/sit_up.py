from core.base_excercise import BaseExcercise


class SitupDetector(BaseExcercise):
    """
    Tracks sit-ups via the torso angle (shoulder-hip-knee).
    Lying flat → large angle; sitting up → small angle.

    Metrics:
        torso_angle      — shoulder-hip-knee
        hip_flexor_status — whether hips are anchored / knees bent properly
        neck_status       — head in neutral (ear near shoulder line)
        back_angle        — same as torso_angle alias used in session state
    """

    DOWN_THRESHOLD = 140   # mostly flat
    UP_THRESHOLD = 80      # sitting upright
    MIN_VISIBILITY = 0.6

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_EAR = 7
    RIGHT_EAR = 8

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_HIP].visibility
        right_vis = landmarks[self.RIGHT_HIP].visibility

        if left_vis >= right_vis:
            shoulder_idx, hip_idx, knee_idx, ankle_idx = (
                self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE
            )
            ear_idx = self.LEFT_EAR
        else:
            shoulder_idx, hip_idx, knee_idx, ankle_idx = (
                self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE
            )
            ear_idx = self.RIGHT_EAR

        torso_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        back_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        key_visible = (
            landmarks[shoulder_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[hip_idx].visibility >= self.MIN_VISIBILITY
            and landmarks[knee_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_visible:
            if torso_angle > self.DOWN_THRESHOLD:
                self.stage = "down"
            if torso_angle < self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Hip flexor: knee angle (hip-knee-ankle) should be bent ~90°
        knee_angle = self.calculate_angle(
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
            self.get_point(landmarks, ankle_idx),
        )
        if 70 <= knee_angle <= 110:
            hip_flexor_status = "GOOD"
        elif knee_angle < 70:
            hip_flexor_status = "OVER-BENT"
        else:
            hip_flexor_status = "STRAIGHTEN KNEES"

        # Neck: ear should stay roughly above shoulder (x proximity)
        ear_x = landmarks[ear_idx].x
        shoulder_x = landmarks[shoulder_idx].x
        neck_status = "NEUTRAL" if abs(ear_x - shoulder_x) < 0.08 else "FORWARD"

        return {
            "reps": self.reps,
            "torso_angle": int(torso_angle),
            "back_angle": int(back_angle),
            "hip_flexor_status": hip_flexor_status,
            "neck_status": neck_status,
        }