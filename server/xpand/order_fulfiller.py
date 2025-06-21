from __future__ import annotations

import asyncio

from xpand.models import Order
from xpand.services import InventoryDb
from xpand.services import Robot

from server.xpand.models.robotic_arm_motion import RoboticArmMotion
from server.xpand.models.slot import Slot

DANGER_ZONE_START = 1000
DANGER_ZONE_END = 2000


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

    async def _move_safely(self, target_slot: Slot):
        current_x, current_y = await self.robot.get_position()
        target_x, target_y = target_slot.x, target_slot.y

        # Scenario 1: Passing completely through danger zone
        if (current_x < DANGER_ZONE_START and target_x > DANGER_ZONE_END) or (
            current_x > DANGER_ZONE_END and target_x < DANGER_ZONE_START
        ):

            # Start folding while beginning to move toward first boundary
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

            # Move through danger zone (already folded)
            await self.robot.move_to(
                DANGER_ZONE_END if current_x < DANGER_ZONE_START else DANGER_ZONE_START,
                current_y,
            )

            # Move to final position and unfold
            await asyncio.gather(
                self.robot.move_to(target_x, target_y),
                self.robot.execute_motion(RoboticArmMotion.UNFOLD),
            )

        # Scenario 2: Entering danger zone but not exiting
        elif (
            current_x < DANGER_ZONE_START
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ) or (
            current_x > DANGER_ZONE_END
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ):

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

        # Scenario 3: Exiting danger zone
        elif (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and target_x < DANGER_ZONE_START
        ) or (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and target_x > DANGER_ZONE_END
        ):

            await self.robot.move_to(
                DANGER_ZONE_START if target_x < DANGER_ZONE_START else DANGER_ZONE_END,
                current_y,
            )
            await asyncio.gather(
                self.robot.move_to(target_x, target_y),
                self.robot.execute_motion(RoboticArmMotion.UNFOLD),
            )

        # Scenario 4: Moving within danger zone
        elif (
            DANGER_ZONE_START <= current_x <= DANGER_ZONE_END
            and DANGER_ZONE_START <= target_x <= DANGER_ZONE_END
        ):

            await self.robot.move_to(target_x, target_y)

        # Scenario 5: Safe movement (no danger zone interaction)
        else:
            await self.robot.move_to(target_x, target_y)

    async def _move_to_start_of_danger_while_folding(
        self, start_of_danger: tuple[int, int],
    ):
        await asyncio.gather(
            self.robot.execute_motion(RoboticArmMotion.FOLD),
            self.robot.move_to(start_of_danger),
        )

    async def _move_to_destination_while_unfolding(self, destination: Slot):
        await asyncio.gather(
            self.robot.move_to(destination.x, destination.y),
            self.robot.execute_motion(RoboticArmMotion.UNFOLD),
        )

    async def _get_item_from_safe_slot(self, slot: Slot, item: str) -> bool:
        await self.robot.move_to(slot.x, slot.y)
