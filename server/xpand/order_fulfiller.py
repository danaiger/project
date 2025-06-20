from __future__ import annotations

import asyncio

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.robotic_arm_motion import RoboticArmMotion
from server.xpand.models.slot import Slot

START = 1000
END = 2000


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory

    async def fulfill_order(self, order: Order):
        items_to_possible_slots = self._get_items_to_possible_slots_dict(order)
        items = items_to_possible_slots.keys()
        for item in items:
            self._get_individual_item(item, items_to_possible_slots)

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
            start, end = self.get_dangerous_zone_start_end_x(
                slot, current_position,
            )

            if not start and not end:
                picked = await self._get_item_from_safe_slot(slot, item)
                if picked:
                    return True
                else:
                    continue
            elif start:
                await self._move_to_start_of_danger_while_folding(start, current_position[1])
                if end:
                    await self.robot.move_to(end, current_position[1])
                    await self._move_to_destination_while_unfolding(slot)

    def get_dangerous_zone_start_end_x(self, slot_to_reach: Slot, current_position: tuple[int, int]):
        if (slot_to_reach.x >= START and slot_to_reach.x <= END) or (current_position[0] >= START and slot_to_reach[0] <= END):
            if (slot_to_reach.x >= START and slot_to_reach.x <= END) and (current_position[0] >= START and slot_to_reach[0] <= END):
                return (current_position[0], None)
            elif (slot_to_reach.x >= START and slot_to_reach.x <= END):
                if current_position[0] < START:
                    return (START, None)
                elif current_position[0] > END:
                    return (END, None)
        elif slot_to_reach.x < START and current_position[0] > END:
            return (END, START)
        elif slot_to_reach.x > END and current_position[0] < START:
            return (START, END)
        return None, None

    async def _move_to_start_of_danger_while_folding(self, start_of_danger: tuple[int, int]):
        await asyncio.gather(self.robot.execute_motion(RoboticArmMotion.FOLD), self.robot.move_to(start_of_danger))

    async def _move_to_destination_while_unfolding(self, destination: Slot):
        await asyncio.gather(self.robot.move_to(destination.x, destination.y), self.robot.execute_motion(RoboticArmMotion.UNFOLD))

    async def _get_item_from_safe_slot(self, slot: Slot, item: str) -> bool:
        await self.robot.move_to(slot.x, slot.y)
        picked = await self.robot.execute_motion(RoboticArmMotion.PICK)
        if not picked:
            await self.inventory.flag_slot_error(slot.slot)
            return False
        else:
            await self.inventory.item_picked(slot.slot, item)
            return True
