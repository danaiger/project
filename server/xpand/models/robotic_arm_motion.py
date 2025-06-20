from __future__ import annotations

from enum import Enum


class RoboticArmMotion(Enum):
    PICK = 1
    PLACE_BAG = 2
    FOLD = 10
