"""
Reachy Coach - Robot behaviors for fitness encouragement
Uses Reachy Mini SDK directly for gestures and animations
"""

import asyncio
from typing import Optional
from enum import Enum

from reachy_mini import ReachyMini


class CoachEmotion(Enum):
    """Coach emotions/reactions"""
    READY = "ready"
    ENCOURAGING = "encouraging"
    EXCITED = "excited"
    CELEBRATING = "celebrating"
    COUNTING = "counting"


class ReachyCoach:
    """
    Controls Reachy Mini to act as a fitness coach.
    Uses the SDK directly for better integration.
    """

    def __init__(self, reachy_mini: Optional[ReachyMini] = None):
        self.reachy = reachy_mini
        self._current_emotion = CoachEmotion.READY

    @property
    def is_connected(self) -> bool:
        """Check if Reachy is available."""
        return self.reachy is not None

    async def _move_head(self, yaw: float = 0, pitch: float = 0, roll: float = 0, duration: float = 0.5):
        """Move head to position."""
        if not self.reachy:
            return
        try:
            # Convert to look_at coordinates (approximate)
            x = 0.5  # Forward
            y = yaw * 0.3  # Left/right
            z = pitch * 0.2  # Up/down
            self.reachy.head.look_at(x=x, y=y, z=z, duration=duration)
            await asyncio.sleep(duration)
        except Exception as e:
            print(f"Head move error: {e}")

    async def _move_antennas(self, left: float = 0, right: float = 0, duration: float = 0.3):
        """Move antennas to position (-1 to 1 scale, converted to degrees)."""
        if not self.reachy:
            return
        try:
            # Convert -1 to 1 scale to degrees (-45 to 45)
            left_deg = left * 45
            right_deg = right * 45
            self.reachy.head.left_antenna.goal_position = left_deg
            self.reachy.head.right_antenna.goal_position = right_deg
            await asyncio.sleep(duration)
        except Exception as e:
            print(f"Antenna move error: {e}")

    async def nod_yes(self):
        """Nod head yes - encouragement."""
        if not self.reachy:
            return
        try:
            for _ in range(2):
                self.reachy.head.look_at(x=0.5, y=0, z=0.1, duration=0.15)
                await asyncio.sleep(0.15)
                self.reachy.head.look_at(x=0.5, y=0, z=-0.05, duration=0.15)
                await asyncio.sleep(0.15)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
        except Exception as e:
            print(f"Nod error: {e}")

    async def shake_no(self):
        """Shake head no - form correction."""
        if not self.reachy:
            return
        try:
            for _ in range(2):
                self.reachy.head.look_at(x=0.5, y=0.15, z=0, duration=0.12)
                await asyncio.sleep(0.12)
                self.reachy.head.look_at(x=0.5, y=-0.15, z=0, duration=0.12)
                await asyncio.sleep(0.12)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
        except Exception as e:
            print(f"Shake error: {e}")

    async def wiggle_antennas(self):
        """Wiggle antennas - excitement."""
        if not self.reachy:
            return
        try:
            for _ in range(3):
                self.reachy.head.left_antenna.goal_position = 35
                self.reachy.head.right_antenna.goal_position = -35
                await asyncio.sleep(0.1)
                self.reachy.head.left_antenna.goal_position = -35
                self.reachy.head.right_antenna.goal_position = 35
                await asyncio.sleep(0.1)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Wiggle error: {e}")

    async def celebration_dance(self):
        """Celebration for reaching target."""
        if not self.reachy:
            return
        try:
            # Happy antenna wiggle
            await self.wiggle_antennas()

            # Head bobbing
            for _ in range(3):
                self.reachy.head.look_at(x=0.5, y=0.1, z=0.1, duration=0.2)
                self.reachy.head.left_antenna.goal_position = 20
                self.reachy.head.right_antenna.goal_position = -20
                await asyncio.sleep(0.2)
                self.reachy.head.look_at(x=0.5, y=-0.1, z=-0.05, duration=0.2)
                self.reachy.head.left_antenna.goal_position = -20
                self.reachy.head.right_antenna.goal_position = 20
                await asyncio.sleep(0.2)

            # Final pose - antennas up
            self.reachy.head.look_at(x=0.5, y=0, z=0.05, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 30
            self.reachy.head.right_antenna.goal_position = 30
            await asyncio.sleep(0.5)

            # Reset
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.5)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Celebration error: {e}")

    async def count_rep(self, rep_number: int):
        """Quick acknowledgment of a rep."""
        if not self.reachy:
            return
        try:
            # Quick nod with antenna pop
            self.reachy.head.look_at(x=0.5, y=0, z=0.08, duration=0.1)
            self.reachy.head.left_antenna.goal_position = 15
            self.reachy.head.right_antenna.goal_position = 15
            await asyncio.sleep(0.1)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.15)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Count rep error: {e}")

    async def encourage(self):
        """Encouraging movement during exercise."""
        if not self.reachy:
            return
        try:
            self.reachy.head.look_at(x=0.5, y=0.05, z=0, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 10
            self.reachy.head.right_antenna.goal_position = 10
            await asyncio.sleep(0.3)
            self.reachy.head.look_at(x=0.5, y=-0.05, z=0, duration=0.3)
            await asyncio.sleep(0.3)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Encourage error: {e}")

    async def get_ready_pose(self):
        """Ready/waiting pose."""
        if not self.reachy:
            return
        try:
            self.reachy.head.look_at(x=0.5, y=0, z=0.02, duration=0.5)
            self.reachy.head.left_antenna.goal_position = 5
            self.reachy.head.right_antenna.goal_position = 5
        except Exception as e:
            print(f"Ready pose error: {e}")

    async def watching_pose(self):
        """Attentive watching pose."""
        if not self.reachy:
            return
        try:
            self.reachy.head.look_at(x=0.5, y=0, z=-0.05, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 15
            self.reachy.head.right_antenna.goal_position = 15
        except Exception as e:
            print(f"Watching pose error: {e}")

    async def impatient_wiggle(self):
        """Impatient/annoyed wiggle when user is slacking."""
        if not self.reachy:
            return
        try:
            # Quick side-to-side head shake with antenna droop
            for _ in range(2):
                self.reachy.head.look_at(x=0.5, y=0.12, z=-0.05, duration=0.15)
                self.reachy.head.left_antenna.goal_position = -20
                self.reachy.head.right_antenna.goal_position = -20
                await asyncio.sleep(0.15)
                self.reachy.head.look_at(x=0.5, y=-0.12, z=-0.05, duration=0.15)
                await asyncio.sleep(0.15)
            # End with a "hmph" pose
            self.reachy.head.look_at(x=0.5, y=0, z=-0.08, duration=0.2)
            self.reachy.head.left_antenna.goal_position = -10
            self.reachy.head.right_antenna.goal_position = -10
            await asyncio.sleep(0.5)
            # Reset
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Impatient wiggle error: {e}")

    async def excited_bounce(self):
        """Excited bouncing motion for big achievements."""
        if not self.reachy:
            return
        try:
            for _ in range(4):
                self.reachy.head.look_at(x=0.5, y=0, z=0.12, duration=0.1)
                self.reachy.head.left_antenna.goal_position = 40
                self.reachy.head.right_antenna.goal_position = 40
                await asyncio.sleep(0.1)
                self.reachy.head.look_at(x=0.5, y=0, z=-0.02, duration=0.1)
                self.reachy.head.left_antenna.goal_position = -10
                self.reachy.head.right_antenna.goal_position = -10
                await asyncio.sleep(0.1)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Excited bounce error: {e}")

    async def head_tilt_curious(self):
        """Curious head tilt."""
        if not self.reachy:
            return
        try:
            self.reachy.head.look_at(x=0.5, y=0.1, z=0.05, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 25
            self.reachy.head.right_antenna.goal_position = 5
            await asyncio.sleep(0.8)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.3)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Head tilt error: {e}")

    async def double_nod(self):
        """Enthusiastic double nod."""
        if not self.reachy:
            return
        try:
            for _ in range(2):
                self.reachy.head.look_at(x=0.5, y=0, z=0.1, duration=0.12)
                await asyncio.sleep(0.12)
                self.reachy.head.look_at(x=0.5, y=0, z=-0.05, duration=0.12)
                await asyncio.sleep(0.12)
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.15)
        except Exception as e:
            print(f"Double nod error: {e}")

    async def look_right(self):
        """Turn head to the right with antenna movement."""
        if not self.reachy:
            return
        try:
            # Turn right with expressive antenna
            self.reachy.head.look_at(x=0.5, y=-0.2, z=0.05, duration=0.25)
            self.reachy.head.left_antenna.goal_position = 20
            self.reachy.head.right_antenna.goal_position = -15
            await asyncio.sleep(0.4)
            # Return to center
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Look right error: {e}")

    async def look_left(self):
        """Turn head to the left with antenna movement."""
        if not self.reachy:
            return
        try:
            # Turn left with expressive antenna
            self.reachy.head.look_at(x=0.5, y=0.2, z=0.05, duration=0.25)
            self.reachy.head.left_antenna.goal_position = -15
            self.reachy.head.right_antenna.goal_position = 20
            await asyncio.sleep(0.4)
            # Return to center
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.2)
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
        except Exception as e:
            print(f"Look left error: {e}")

    async def super_excited_antennas(self):
        """SUPER excited antenna celebration for completing exercise!"""
        if not self.reachy:
            return
        try:
            # Fast wild antenna wiggle + head bobbing
            for _ in range(5):
                # Antennas go crazy
                self.reachy.head.left_antenna.goal_position = 45
                self.reachy.head.right_antenna.goal_position = -45
                self.reachy.head.look_at(x=0.5, y=0.08, z=0.1, duration=0.08)
                await asyncio.sleep(0.08)
                self.reachy.head.left_antenna.goal_position = -45
                self.reachy.head.right_antenna.goal_position = 45
                self.reachy.head.look_at(x=0.5, y=-0.08, z=0.1, duration=0.08)
                await asyncio.sleep(0.08)

            # Victory pose - both antennas UP high!
            self.reachy.head.left_antenna.goal_position = 45
            self.reachy.head.right_antenna.goal_position = 45
            self.reachy.head.look_at(x=0.5, y=0, z=0.15, duration=0.3)
            await asyncio.sleep(0.8)

            # Spin antennas in opposite directions
            for _ in range(3):
                self.reachy.head.left_antenna.goal_position = 40
                self.reachy.head.right_antenna.goal_position = -40
                await asyncio.sleep(0.12)
                self.reachy.head.left_antenna.goal_position = -40
                self.reachy.head.right_antenna.goal_position = 40
                await asyncio.sleep(0.12)

            # Final triumphant pose
            self.reachy.head.left_antenna.goal_position = 30
            self.reachy.head.right_antenna.goal_position = 30
            self.reachy.head.look_at(x=0.5, y=0, z=0.05, duration=0.3)
            await asyncio.sleep(0.5)

            # Reset
            self.reachy.head.left_antenna.goal_position = 0
            self.reachy.head.right_antenna.goal_position = 0
            self.reachy.head.look_at(x=0.5, y=0, z=0, duration=0.3)
        except Exception as e:
            print(f"Super excited error: {e}")

    async def react_to_rep(self, rep_count: int, target: int):
        """React based on rep count with alternating head movements.

        - Odd reps: look left
        - Even reps: look right
        - Target reached: super excited antenna celebration!
        """
        if rep_count >= target:
            # TARGET REACHED! Go absolutely crazy with excitement!
            await self.super_excited_antennas()
            await self.celebration_dance()
        elif rep_count == target - 1:
            # Last one! Get excited with alternating look
            if rep_count % 2 == 0:
                await self.look_right()
            else:
                await self.look_left()
            await self.excited_bounce()
        else:
            # Alternate head direction based on rep count
            if rep_count % 2 == 0:
                # Even rep - look right
                await self.look_right()
            else:
                # Odd rep - look left
                await self.look_left()

            # Add extra flair for milestones
            if rep_count % 5 == 0:
                await self.wiggle_antennas()
