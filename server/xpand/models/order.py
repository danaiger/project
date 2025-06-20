from __future__ import annotations

from dataclasses import dataclass

from xpand.models import Item


@dataclass
class Order:
    id: str
    items: list[Item]
