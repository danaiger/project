from __future__ import annotations

from typing import Set

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.slot import Slot


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory

    async def fulfill_order(self, order: Order):
        slots = self._get_slots_by_order(order)

    def _get_slots_by_order(self, order: Order) -> Set[Slot]:
        all_slots = []
        for item in order.items:
            slots = self.inventory.find_slots_by_sku(item.sku)
            all_slots.extend(slots)
        return set(all_slots)
