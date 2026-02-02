"""
Exercise Tracking - Detects and counts exercise repetitions
Supports squats, arm raises, and jumping jacks
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
import time


class ExercisePhase(Enum):
    """Current phase of movement"""
    READY = "ready"          # Starting position
    MOVING = "moving"        # In motion
    PEAK = "peak"            # At peak position
    RETURNING = "returning"  # Returning to start


class ExerciseType(Enum):
    """Supported exercise types"""
    SQUATS = "squats"
    ARM_RAISES = "arm_raises"
    JUMPING_JACKS = "jumping_jacks"


@dataclass
class ExerciseState:
    """Current state of exercise tracking"""
    exercise_type: ExerciseType = ExerciseType.SQUATS
    exercise_name: str = "Squats"
    rep_count: int = 0
    target_reps: int = 10
    phase: ExercisePhase = ExercisePhase.READY
    current_angle: float = 180.0
    is_active: bool = False
    started_at: Optional[float] = None
    last_rep_at: Optional[float] = None
    feedback: str = "Get ready!"


class ExerciseTracker:
    """
    Universal exercise tracker supporting multiple exercise types.
    """

    # Squat thresholds (knee angle)
    SQUAT_STANDING = 160
    SQUAT_BOTTOM = 120

    # Arm raise thresholds (shoulder angle - arm relative to torso)
    ARM_DOWN = 50           # Arms at sides
    ARM_UP = 150            # Arms raised high

    # Jumping jack thresholds
    JACK_CLOSED = 40        # Arms down, legs together
    JACK_OPEN = 120         # Arms up, legs apart

    EXERCISE_NAMES = {
        ExerciseType.SQUATS: "Squats",
        ExerciseType.ARM_RAISES: "Arm Raises",
        ExerciseType.JUMPING_JACKS: "Jumping Jacks"
    }

    def __init__(self, target_reps: int = 10, exercise_type: ExerciseType = ExerciseType.SQUATS):
        self.target_reps = target_reps
        self.exercise_type = exercise_type
        self.state = ExerciseState(
            target_reps=target_reps,
            exercise_type=exercise_type,
            exercise_name=self.EXERCISE_NAMES[exercise_type]
        )
        self.prev_angle = 180.0
        self.on_rep_complete: Optional[Callable[[int], None]] = None
        self.on_target_reached: Optional[Callable[[], None]] = None

    def set_exercise(self, exercise_type: ExerciseType):
        """Change exercise type."""
        self.exercise_type = exercise_type
        self.state.exercise_type = exercise_type
        self.state.exercise_name = self.EXERCISE_NAMES[exercise_type]

    def start(self):
        """Start tracking session"""
        self.state = ExerciseState(
            target_reps=self.target_reps,
            exercise_type=self.exercise_type,
            exercise_name=self.EXERCISE_NAMES[self.exercise_type],
            is_active=True,
            started_at=time.time(),
            feedback=f"Let's go! Start your {self.EXERCISE_NAMES[self.exercise_type]}!"
        )
        self.prev_angle = 180.0 if self.exercise_type == ExerciseType.SQUATS else 0.0

    def stop(self):
        """Stop tracking session"""
        self.state.is_active = False
        duration = time.time() - (self.state.started_at or time.time())
        self.state.feedback = f"Great workout! {self.state.rep_count} reps in {duration:.0f}s"

    def reset(self):
        """Reset counter"""
        self.state = ExerciseState(
            target_reps=self.target_reps,
            exercise_type=self.exercise_type,
            exercise_name=self.EXERCISE_NAMES[self.exercise_type]
        )
        self.prev_angle = 180.0 if self.exercise_type == ExerciseType.SQUATS else 0.0

    def update(self, angle: float, secondary_angle: float = None) -> ExerciseState:
        """
        Update tracker with new angle reading.
        - For squats: angle = knee angle
        - For arm raises: angle = shoulder angle (arm-torso)
        - For jumping jacks: angle = shoulder angle, secondary_angle = hip spread
        """
        if not self.state.is_active:
            return self.state

        self.state.current_angle = angle

        if self.exercise_type == ExerciseType.SQUATS:
            self._update_squats(angle)
        elif self.exercise_type == ExerciseType.ARM_RAISES:
            self._update_arm_raises(angle)
        elif self.exercise_type == ExerciseType.JUMPING_JACKS:
            self._update_jumping_jacks(angle)

        self.prev_angle = angle
        return self.state

    def _update_squats(self, knee_angle: float):
        """Track squat reps using knee angle."""
        if self.state.phase == ExercisePhase.READY:
            if knee_angle < self.SQUAT_STANDING:
                self.state.phase = ExercisePhase.MOVING
                self.state.feedback = "Going down... keep going!"

        elif self.state.phase == ExercisePhase.MOVING:
            if knee_angle <= self.SQUAT_BOTTOM:
                self.state.phase = ExercisePhase.PEAK
                self.state.feedback = "Great depth! Now push up!"
            elif knee_angle > self.SQUAT_STANDING:
                self.state.phase = ExercisePhase.READY
                self.state.feedback = "Go deeper! Aim for parallel."

        elif self.state.phase == ExercisePhase.PEAK:
            if knee_angle > self.SQUAT_BOTTOM:
                self.state.phase = ExercisePhase.RETURNING
                self.state.feedback = "Push! Push! Almost there!"

        elif self.state.phase == ExercisePhase.RETURNING:
            if knee_angle >= self.SQUAT_STANDING:
                self._complete_rep()
            elif knee_angle < self.SQUAT_BOTTOM:
                self.state.phase = ExercisePhase.PEAK

    def _update_arm_raises(self, shoulder_angle: float):
        """Track arm raise reps using shoulder angle."""
        if self.state.phase == ExercisePhase.READY:
            if shoulder_angle > self.ARM_DOWN + 30:
                self.state.phase = ExercisePhase.MOVING
                self.state.feedback = "Raising those arms! Keep going!"

        elif self.state.phase == ExercisePhase.MOVING:
            if shoulder_angle >= self.ARM_UP:
                self.state.phase = ExercisePhase.PEAK
                self.state.feedback = "Arms up! Beautiful! Now bring them down!"
            elif shoulder_angle < self.ARM_DOWN:
                self.state.phase = ExercisePhase.READY
                self.state.feedback = "Raise them higher! Reach for the sky!"

        elif self.state.phase == ExercisePhase.PEAK:
            if shoulder_angle < self.ARM_UP - 20:
                self.state.phase = ExercisePhase.RETURNING
                self.state.feedback = "Lowering... nice and controlled!"

        elif self.state.phase == ExercisePhase.RETURNING:
            if shoulder_angle <= self.ARM_DOWN:
                self._complete_rep()
            elif shoulder_angle >= self.ARM_UP:
                self.state.phase = ExercisePhase.PEAK

    def _update_jumping_jacks(self, shoulder_angle: float):
        """Track jumping jack reps using shoulder angle."""
        if self.state.phase == ExercisePhase.READY:
            if shoulder_angle > self.JACK_CLOSED + 30:
                self.state.phase = ExercisePhase.MOVING
                self.state.feedback = "Jump! Spread those arms!"

        elif self.state.phase == ExercisePhase.MOVING:
            if shoulder_angle >= self.JACK_OPEN:
                self.state.phase = ExercisePhase.PEAK
                self.state.feedback = "Wide open! Now close it up!"
            elif shoulder_angle < self.JACK_CLOSED:
                self.state.phase = ExercisePhase.READY

        elif self.state.phase == ExercisePhase.PEAK:
            if shoulder_angle < self.JACK_OPEN - 30:
                self.state.phase = ExercisePhase.RETURNING
                self.state.feedback = "Closing! Keep the rhythm!"

        elif self.state.phase == ExercisePhase.RETURNING:
            if shoulder_angle <= self.JACK_CLOSED:
                self._complete_rep()
            elif shoulder_angle >= self.JACK_OPEN:
                self.state.phase = ExercisePhase.PEAK

    def _complete_rep(self):
        """Complete a repetition."""
        self.state.phase = ExercisePhase.READY
        self.state.rep_count += 1
        self.state.last_rep_at = time.time()

        reps_left = self.target_reps - self.state.rep_count
        if self.state.rep_count >= self.target_reps:
            self.state.feedback = f"TARGET REACHED! {self.state.rep_count} reps! YOU'RE A LEGEND!"
            if self.on_target_reached:
                self.on_target_reached()
        elif reps_left <= 3:
            self.state.feedback = f"{self.state.rep_count}! Only {reps_left} more! FINISH STRONG!"
        elif self.state.rep_count == 1:
            self.state.feedback = "1! HERE WE GO! Keep it up!"
        elif self.state.rep_count % 5 == 0:
            self.state.feedback = f"{self.state.rep_count}! CRUSHING IT! Stay strong!"
        else:
            self.state.feedback = f"{self.state.rep_count}! NICE ONE!"

        if self.on_rep_complete:
            self.on_rep_complete(self.state.rep_count)

    def get_progress(self) -> float:
        """Get progress as percentage (0-100)"""
        if self.target_reps == 0:
            return 100.0
        return min(100.0, (self.state.rep_count / self.target_reps) * 100)

    def get_duration(self) -> float:
        """Get elapsed time in seconds"""
        if not self.state.started_at:
            return 0.0
        return time.time() - self.state.started_at


# Backwards compatibility alias
SquatTracker = ExerciseTracker
SquatPhase = ExercisePhase
