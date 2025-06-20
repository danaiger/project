from __future__ import annotations

from xpand.models import Slot


class InventoryDb:
    def find_slots_by_sku(self, sku: str) -> list[Slot]:
        pass

    def get_slot(self, slot: str) -> Slot:
        pass

    def item_picked(self, slot: str, sku: str):
        pass

    def flag_slot_error(self, slot: str):
        pass
