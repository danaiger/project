from __future__ import annotations

from xpand.models.robotic_arm_motion import RoboticArmMotion


class Robot:
    async def get_position(self) -> (int, int):
        pass

    async def move_to(self, x: int, y: int):
        pass

    async def execute_motion(self, motion: RoboticArmMotion) -> bool:
        pass
