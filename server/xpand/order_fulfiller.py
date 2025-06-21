from __future__ import annotations

import asyncio

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.robotic_arm_motion import RoboticArmMotion
from server.xpand.models.slot import Slot

DANGER_ZONE_START = 1000
DANGER_ZONE_END = 2000
PLACING_SLOT = 'A0.3.0'


class OrderFulfiller:

    def __init__(self, robot: Robot, inventory: InventoryDb):
        self.robot = robot
        self.inventory = inventory
        self._placing_slot_coordinates = self.inventory.get_slot(PLACING_SLOT)
        self.placing_slot = Slot(
            PLACING_SLOT, self._placing_slot_coordinates.x, self._placing_slot_coordinates.y,
        )

    async def fulfill_order(self, order: Order):
        items_to_possible_slots = self._get_items_to_possible_slots_dict(order)
        items = items_to_possible_slots.keys()
        items_picked = []
        for item in items:
            if self._get_individual_item(item, items_to_possible_slots):
                items_picked.append(item)
            else:
                continue
        await self._move_safely(self.placing_slot)
        await self.robot.execute_motion(RoboticArmMotion.PLACE_BAG)

    def _get_items_to_possible_slots_dict(self, order: Order) -> dict[str, list[Slot]]:
        items_to_possible_slots = dict()
        for item in order.items:
            slots = self.inventory.find_slots_by_sku(item.sku)
            items_to_possible_slots[item.sku] = slots

        return items_to_possible_slots

    async def _get_individual_item(
        self, item: str, items_to_possible_slots: dict[str, list[Slot]],
    ) -> bool:
        possible_slots = items_to_possible_slots[item]
        for slot in possible_slots:
            await self._move_safely(slot)
            picked = await self.robot.execute_motion(RoboticArmMotion.PICK)
            if not picked:
                await self.inventory.flag_slot_error(slot.slot)
                continue
            else:
                await self.inventory.item_picked(slot.slot, item)
                return True
        return False

    async def _cross_from_one_side_of_danger_zone_to_target_at_other_side(self, current_x, current_y, target_x, target_y):
        fold_task = asyncio.create_task(
            self.robot.execute_motion(RoboticArmMotion.FOLD),
        )
        await asyncio.gather(
            fold_task,
            self.robot.move_to(
                (
                    DANGER_ZONE_START
                    if current_x < DANGER_ZONE_START
                    else DANGER_ZONE_END
                ),
                current_y,
            ),
        )

        await self.robot.move_to(
            DANGER_ZONE_END if current_x < DANGER_ZONE_START else DANGER_ZONE_START,
            current_y,
        )

        await asyncio.gather(
            self.robot.move_to(target_x, target_y),
            self.robot.execute_motion(RoboticArmMotion.UNFOLD),
        )

    async def _move_to_slot_inside_danger_zone_from_outside(self, current_x, current_y, target_x, target_y):

        await asyncio.gather(
            self.robot.execute_motion(RoboticArmMotion.FOLD),
            self.robot.move_to(
                (
                    DANGER_ZONE_START
                    if current_x < DANGER_ZONE_START
                    else DANGER_ZONE_END
                ),
                current_y,
            ),
        )

        await self.robot.move_to(target_x, target_y)

    async def _move_from_inside_danger_zone_to_slot_outside(self, current_y, target_x, target_y):
        await self.robot.move_to(
            DANGER_ZONE_START if target_x < DANGER_ZONE_START else DANGER_ZONE_END,
            current_y,
        )
        await asyncio.gather(
            self.robot.move_to(target_x, target_y),
            self.robot.execute_motion(RoboticArmMotion.UNFOLD),
        )

    async def _move_without_switching_boundaries(self, target_x, target_y):
        await self.robot.move_to(target_x, target_y)

    async def _move_safely(self, target_slot: Slot):
        current_x, current_y = await self.robot.get_position()
        target_x, target_y = target_slot.x, target_slot.y

        if (current_x < DANGER_ZONE_START and target_x > DANGER_ZONE_END) or (
            current_x > DANGER_ZONE_END and target_x < DANGER_ZONE_START
        ):
            await self._cross_from_one_side_of_danger_zone_to_target_at_other_side(current_x, current_y, target_x, target_y)

        elif (
            current_x < DANGER_ZONE_START
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ) or (
            current_x > DANGER_ZONE_END
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ):
            await self._move_to_slot_inside_danger_zone_from_outside(current_x, current_y, target_x, target_y)

        elif (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and target_x < DANGER_ZONE_START
        ) or (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and target_x > DANGER_ZONE_END
        ):
            await self._move_from_inside_danger_zone_to_slot_outside(current_y, target_x, target_y)

        elif (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ):

            await self._move_without_switching_boundaries(target_x, target_y)

        else:
            await self._move_without_switching_boundaries(target_x, target_y)
