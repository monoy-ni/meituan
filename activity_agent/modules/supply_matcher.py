from __future__ import annotations

from activity_agent.data import SUPPLY_CATALOG
from activity_agent.domain.models import MerchantSupply, ThemeSlot, UserRequest


class SupplyMatcher:
    """Selects local supplies for each theme slot under budget and preference constraints."""

    def __init__(self, catalog: list[MerchantSupply] | None = None) -> None:
        self.catalog = catalog or SUPPLY_CATALOG

    def match_slot(self, slot: ThemeSlot, request: UserRequest, used_ids: set[str]) -> MerchantSupply:
        candidates = [
            supply
            for supply in self.catalog
            if supply.available
            and supply.id not in used_ids
            and supply.type == slot.type
            and request.scene in supply.scene_fit
            and self._passes_constraints(supply, request)
        ]
        if not candidates:
            candidates = [
                supply
                for supply in self.catalog
                if supply.available and supply.id not in used_ids and supply.type == slot.type and request.scene in supply.scene_fit
            ]
        if not candidates:
            raise ValueError(f"No supply candidate for slot type {slot.type}")

        per_slot_budget = max(40, int(request.budget_per_person / 3) + 60)
        return max(
            candidates,
            key=lambda supply: self._score_supply(supply, slot, request, per_slot_budget),
        )

    def _passes_constraints(self, supply: MerchantSupply, request: UserRequest) -> bool:
        constraints = request.hard_constraints
        if constraints.get("no_alcohol") and ("微醺" in supply.tags or "酒" in supply.name):
            return False
        if constraints.get("indoor_only") and "室内" not in supply.tags and supply.type.value not in {"dining", "hotel", "gift"}:
            return False
        if constraints.get("quiet") and ("热闹" in supply.tags or "发疯" in supply.tags):
            return False
        if request.relationship_stage == "暧昧/追求中" and supply.type.value == "hotel":
            return False
        return True

    def _score_supply(self, supply: MerchantSupply, slot: ThemeSlot, request: UserRequest, per_slot_budget: int) -> int:
        desired_score = 6 * len(set(supply.tags) & set(slot.desired_tags))
        mood_score = 3 * len(set(supply.tags) & set(request.mood_tags))
        price_score = 5 if supply.price <= per_slot_budget else -min(8, int((supply.price - per_slot_budget) / 30))
        distance_score = max(0, 4 - int(supply.distance_km))
        booking_score = 2 if any(mode in supply.booking_modes for mode in ["reservation", "ticket", "group_buy", "hotel"]) else 0
        return desired_score + mood_score + price_score + distance_score + booking_score

