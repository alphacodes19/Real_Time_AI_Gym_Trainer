"""
Central registry mapping each user-facing exercise name to its detector class.

Adding a new exercise to the app means:
    1. Writing a new `<name>_detector.py` module in this package (subclass BaseExercise).
    2. Importing the class below and adding one line to DETECTOR_REGISTRY.
    3. Adding the exercise name to EXERCISE_OPTIONS and an entry to METRICS_FIELDS
       in services/config/workout_config.py.

Everything else (video processor, sidebar metrics, session defaults) reads from
DETECTOR_REGISTRY / METRICS_FIELDS and does not need to change.
"""

from detectors.squat_detector import SquatDetector
from detectors.pushup_detector import PushUpDetector
from detectors.bicep_curl_detector import BicepsCurlDetector
from detectors.shoulder_press_detector import ShoulderPressDetector
from detectors.lunge_detector import LungesDetector
from detectors.bench_press_detector import BenchPressDetector
from detectors.burpee_detector import BurpeeDetector
from detectors.butt_kick_detector import ButtKickDetector
from detectors.deadlift_detector import DeadliftDetector
from detectors.dip_detector import DipDetector
from detectors.high_knee_detector import HighKneeDetector
from detectors.jumping_jack_detector import JumpingJackDetector
from detectors.mountain_climber_detector import MountainClimberDetector
from detectors.plank_detector import PlankDetector
from detectors.pullup_detector import PullupDetector
from detectors.situp_detector import SitupDetector


DETECTOR_REGISTRY = {
    "Squats": SquatDetector,
    "Push-ups": PushUpDetector,
    "Biceps Curls (Dumbbell)": BicepsCurlDetector,
    "Shoulder Press": ShoulderPressDetector,
    "Lunges": LungesDetector,
    "Bench Press": BenchPressDetector,
    "Burpees": BurpeeDetector,
    "Butt Kicks": ButtKickDetector,
    "Deadlifts": DeadliftDetector,
    "Dips": DipDetector,
    "High Knees": HighKneeDetector,
    "Jumping Jacks": JumpingJackDetector,
    "Mountain Climbers": MountainClimberDetector,
    "Plank": PlankDetector,
    "Pull-ups": PullupDetector,
    "Sit-ups": SitupDetector,
}
