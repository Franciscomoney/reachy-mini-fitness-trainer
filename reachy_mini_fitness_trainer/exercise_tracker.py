"""
Exercise Tracking - Detects and counts exercise repetitions
Supports squats with plans to add more exercises
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
import time


class SquatPhase(Enum):
    """Current phase of squat movement"""
    STANDING = "standing"      # Knees extended (>160°)
    DESCENDING = "descending"  # Going down
    BOTTOM = "bottom"          # At bottom position (<120°)
    ASCENDING = "ascending"    # Coming back up


@dataclass
class ExerciseState:
    """Current state of exercise tracking"""
    exercise_name: str = "squats"
    rep_count: int = 0
    target_reps: int = 10
    phase: SquatPhase = SquatPhase.STANDING
    current_angle: float = 180.0
    is_active: bool = False
    started_at: Optional[float] = None
    last_rep_at: Optional[float] = None
    feedback: str = "Get ready!"


class SquatTracker:
    """
    Tracks squat repetitions using knee angle

    Squat cycle:
    1. Standing (knee angle > 160°)
    2. Descending (angle decreasing)
    3. Bottom (knee angle < 120°)
    4. Ascending (angle increasing)
    5. Back to Standing = 1 rep complete
    """

    # Angle thresholds
    STANDING_ANGLE = 160  # Above this = standing
    SQUAT_ANGLE = 120     # Below this = squat position

    def __init__(self, target_reps: int = 10):
        self.target_reps = target_reps
        self.state = ExerciseState(target_reps=target_reps)
        self.prev_angle = 180.0
        self.on_rep_complete: Optional[Callable[[int], None]] = None
        self.on_target_reached: Optional[Callable[[], None]] = None

    def start(self):
        """Start tracking session"""
        self.state = ExerciseState(
            target_reps=self.target_reps,
            is_active=True,
            started_at=time.time(),
            feedback="Let's go! Start your squats!"
        )
        self.prev_angle = 180.0

    def stop(self):
        """Stop tracking session"""
        self.state.is_active = False
        duration = time.time() - (self.state.started_at or time.time())
        self.state.feedback = f"Great workout! {self.state.rep_count} reps in {duration:.0f}s"

    def reset(self):
        """Reset counter"""
        self.state = ExerciseState(target_reps=self.target_reps)
        self.prev_angle = 180.0

    def update(self, knee_angle: float) -> ExerciseState:
        """
        Update tracker with new knee angle reading
        Returns current state with feedback
        """
        if not self.state.is_active:
            return self.state

        self.state.current_angle = knee_angle
        old_phase = self.state.phase

        # State machine for squat detection
        if self.state.phase == SquatPhase.STANDING:
            if knee_angle < self.STANDING_ANGLE:
                self.state.phase = SquatPhase.DESCENDING
                self.state.feedback = "Going down... keep going!"

        elif self.state.phase == SquatPhase.DESCENDING:
            if knee_angle <= self.SQUAT_ANGLE:
                self.state.phase = SquatPhase.BOTTOM
                self.state.feedback = "Great depth! Now push up!"
            elif knee_angle > self.STANDING_ANGLE:
                # Went back up without reaching bottom - reset
                self.state.phase = SquatPhase.STANDING
                self.state.feedback = "Go deeper! Aim for parallel."

        elif self.state.phase == SquatPhase.BOTTOM:
            if knee_angle > self.SQUAT_ANGLE:
                self.state.phase = SquatPhase.ASCENDING
                self.state.feedback = "Push! Push! Almost there!"

        elif self.state.phase == SquatPhase.ASCENDING:
            if knee_angle >= self.STANDING_ANGLE:
                # Rep complete!
                self.state.phase = SquatPhase.STANDING
                self.state.rep_count += 1
                self.state.last_rep_at = time.time()

                # Generate feedback
                reps_left = self.target_reps - self.state.rep_count
                if self.state.rep_count >= self.target_reps:
                    self.state.feedback = f"TARGET REACHED! {self.state.rep_count} reps! Amazing!"
                    if self.on_target_reached:
                        self.on_target_reached()
                elif reps_left <= 3:
                    self.state.feedback = f"{self.state.rep_count}! Only {reps_left} more! You got this!"
                elif self.state.rep_count == 1:
                    self.state.feedback = "1! Great start! Keep it up!"
                elif self.state.rep_count % 5 == 0:
                    self.state.feedback = f"{self.state.rep_count}! Halfway there! Stay strong!"
                else:
                    self.state.feedback = f"{self.state.rep_count}! Good rep!"

                # Callback
                if self.on_rep_complete:
                    self.on_rep_complete(self.state.rep_count)

            elif knee_angle < self.SQUAT_ANGLE:
                # Went back down
                self.state.phase = SquatPhase.BOTTOM

        self.prev_angle = knee_angle
        return self.state

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
