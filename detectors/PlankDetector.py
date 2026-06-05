from core.base_excercise import BaseExcercise


class PlankDetector(BaseExcercise):
    """
    Planks are timed holds, not reps.
    This detector tracks hold quality and counts each continuous hold
    (start → break) as one "rep" so the rep counter is meaningful.
    """

    GOOD_BACK_ANGLE_MIN  = 160   # shoulder-hip-ankle angle for a flat back
    HIP_DROP_THRESHOLD   = 0.06  # normalised-y difference between hip mid and body midline

    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_HIP,      RIGHT_HIP      = 23, 24
    LEFT_ANKLE,    RIGHT_ANKLE    = 27, 28

    def __init__(self):
        super().__init__()
        self._in_hold = False

    def reset(self):
        self.reps    = 0
        self.stage   = None
        self._in_hold = False

    def process(self, landmarks):
        # use the more-visible side
        if landmarks[self.LEFT_HIP].visibility >= landmarks[self.RIGHT_HIP].visibility:
            s_idx, h_idx, a_idx = self.LEFT_SHOULDER,  self.LEFT_HIP,  self.LEFT_ANKLE
            opp_h               = self.RIGHT_HIP
            opp_s               = self.RIGHT_SHOULDER
        else:
            s_idx, h_idx, a_idx = self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_ANKLE
            opp_h               = self.LEFT_HIP
            opp_s               = self.LEFT_SHOULDER

        back_angle = self.calculate_angle(
            self.get_point(landmarks, s_idx),
            self.get_point(landmarks, h_idx),
            self.get_point(landmarks, a_idx),
        )

        key_visible = (
            landmarks[s_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[h_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[a_idx].visibility >= self.MIN_VISIBILITY
        )

        # ── hold detection / rep counting ─────────────────────────────────────
        is_holding = key_visible and back_angle >= self.GOOD_BACK_ANGLE_MIN - 15
        if is_holding and not self._in_hold:
            self._in_hold = True
            self.stage    = "holding"
        elif not is_holding and self._in_hold:
            self._in_hold = False
            self.reps    += 1          # one completed hold = one rep
            self.stage    = "rest"

        # ── form metrics ─────────────────────────────────────────────────────
        if back_angle >= self.GOOD_BACK_ANGLE_MIN:
            body_alignment = "GOOD"
        elif back_angle >= 145:
            body_alignment = "SLIGHT SAG"
        else:
            body_alignment = "POOR"

        # hip drop: compare hip mid-y to shoulder-ankle midline y
        hip_mid_y  = (landmarks[self.LEFT_HIP].y  + landmarks[self.RIGHT_HIP].y)  / 2
        sh_mid_y   = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2
        ank_mid_y  = (landmarks[self.LEFT_ANKLE].y + landmarks[self.RIGHT_ANKLE].y) / 2
        midline_y  = (sh_mid_y + ank_mid_y) / 2
        hip_diff   = hip_mid_y - midline_y   # positive = hips dropped below midline

        if hip_diff > self.HIP_DROP_THRESHOLD:
            hip_drop_status = "HIPS LOW"
        elif hip_diff < -self.HIP_DROP_THRESHOLD:
            hip_drop_status = "HIPS HIGH"
        else:
            hip_drop_status = "NEUTRAL"

        hip_status = (
            "LEVEL"
            if abs(landmarks[self.LEFT_HIP].y - landmarks[self.RIGHT_HIP].y) < 0.04
            else "TILTED"
        )

        return {
            "reps":             self.reps,
            "back_angle":       int(back_angle),
            "hip_status":       hip_status,
            "body_alignment":   body_alignment,
            "hip_drop_status":  hip_drop_status,
        }