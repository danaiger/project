from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Slot:
    slot: str
    x: int
    y: int
