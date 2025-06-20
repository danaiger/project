from __future__ import annotations

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory

    async def fulfill_order(self, order: Order):
        pass
