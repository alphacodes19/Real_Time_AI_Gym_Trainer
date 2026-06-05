"""
Exercise detector registry.
Maps the exercise name (as used in EXCERCISE_OPTIONS / session state) to its detector class.
Usage:
    from detectors import DETECTOR_REGISTRY
    detector = DETECTOR_REGISTRY["Squats"]()
"""

from detectors.pushup_detector          import PushupDetector
from detectors.squat_detector           import SquatDetector
from detectors.lunge_detector           import LungeDetector
from detectors.plank_detector           import PlankDetector
from detectors.jumping_jack_detector    import JumpingJackDetector
from detectors.burpee_detector          import BurpeeDetector
from detectors.mountain_climber_detector import MountainClimberDetector
from detectors.situp_detector           import SitupDetector
from detectors.dip_detector             import DipDetector
from detectors.high_knee_detector       import HighKneeDetector
from detectors.butt_kick_detector       import ButtKickDetector
from detectors.bicep_curl_detector      import BicepCurlDetector
from detectors.shoulder_press_detector  import ShoulderPressDetector
from detectors.bench_press_detector     import BenchPressDetector
from detectors.deadlift_detector        import DeadliftDetector
from detectors.pullup_detector          import PullupDetector

DETECTOR_REGISTRY: dict[str, type] = {
    "Push-ups":          PushupDetector,
    "Squats":            SquatDetector,
    "Lunges":            LungeDetector,
    "Planks":            PlankDetector,
    "Jumping Jacks":     JumpingJackDetector,
    "Burpees":           BurpeeDetector,
    "Mountain Climbers": MountainClimberDetector,
    "Sit-ups":           SitupDetector,
    "Dips":              DipDetector,
    "High Knees":        HighKneeDetector,
    "Butt Kicks":        ButtKickDetector,
    "Bicep Curls":       BicepCurlDetector,
    "Shoulder Press":    ShoulderPressDetector,
    "Bench Press":       BenchPressDetector,
    "Deadlifts":         DeadliftDetector,
    "Pull-ups":          PullupDetector,
}