from __future__ import annotations

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.slot import Slot


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory

    async def fulfill_order(self, order: Order):
        slots = self._get_items_to_possible_slots_dict(order)

    def _get_items_to_possible_slots_dict(self, order: Order) -> dict[str, list[Slot]]:
        items_to_possible_slots = dict()
        for item in order.items:
            slots = self.inventory.find_slots_by_sku(item.sku)
            items_to_possible_slots[item.sku] = slots

        return items_to_possible_slots
