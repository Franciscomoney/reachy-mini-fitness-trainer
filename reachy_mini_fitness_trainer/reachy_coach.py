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

    async def react_to_rep(self, rep_count: int, target: int):
        """React based on rep count with varied animations."""
        import random

        if rep_count >= target:
            await self.celebration_dance()
        elif rep_count == target - 1:
            # Last one! Get excited!
            await self.excited_bounce()
        elif rep_count == target - 2:
            await self.wiggle_antennas()
        elif rep_count % 5 == 0:
            # Milestone! Big reaction
            await self.double_nod()
            await self.wiggle_antennas()
        elif rep_count % 3 == 0:
            await self.nod_yes()
        else:
            # Vary the reaction
            reaction = random.choice([self.count_rep, self.nod_yes, self.double_nod])
            await reaction(rep_count) if reaction == self.count_rep else await reaction()
