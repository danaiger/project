from __future__ import annotations

import asyncio

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.robotic_arm_motion import RoboticArmMotion
from server.xpand.models.slot import Slot


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory

    async def fulfill_order(self, order: Order):
        items_to_possible_slots = self._get_items_to_possible_slots_dict(order)
        items = items_to_possible_slots.keys()
        for item in items:
            await self.robot.move_to(items_to_possible_slots[item])

    def _get_items_to_possible_slots_dict(self, order: Order) -> dict[str, list[Slot]]:
        items_to_possible_slots = dict()
        for item in order.items:
            slots = self.inventory.find_slots_by_sku(item.sku)
            items_to_possible_slots[item.sku] = slots

        return items_to_possible_slots

    async def _get_individual_item(self, item: str, items_to_possible_slots: dict[str, list[Slot]]) -> bool:
        possible_slots = items_to_possible_slots[item]
        for slot in possible_slots:
            current_position = await self.robot.get_position()
            if not self.is_dangerous(slot, current_position):
                picked = await self._get_item_from_safe_slot(slot, item)
                if picked:
                    return True
                else:
                    continue

    def is_dangerous(self, slot_to_reach: Slot, current_position: tuple[int, int]) -> bool:
        return False

    async def _move_to_start_of_danger_while_folding(self, start_of_danger: tuple[int, int]):
        await asyncio.gather(self.robot.execute_motion(RoboticArmMotion.FOLD), self.robot.move_to(start_of_danger))

    async def _get_item_from_safe_slot(self, slot: Slot, item: str) -> bool:
        await self.robot.move_to(slot.x, slot.y)
        picked = await self.robot.execute_motion(RoboticArmMotion.PICK)
        if not picked:
            await self.inventory.flag_slot_error(slot.slot)
            return False
        else:
            await self.inventory.item_picked(slot.slot, item)
            return True
