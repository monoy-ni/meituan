from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from activity_agent.data import SUPPLY_CATALOG
from activity_agent.domain.models import MerchantSupply, Scene, TimelineType, ToolEvent


@dataclass(frozen=True)
class ToolResult:
    data: object
    event: ToolEvent


class MockMeituanToolClient:
    """Replaceable mock for Meituan merchant, availability, hold, AA, and confirmation APIs."""

    def __init__(self, catalog: list[MerchantSupply] | None = None) -> None:
        self.catalog = catalog or SUPPLY_CATALOG

    def search_merchants(self, filters: dict[str, object]) -> ToolResult:
        started = time.perf_counter()
        scene = Scene(str(filters["scene"])) if filters.get("scene") else None
        item_type = TimelineType(str(filters["type"])) if filters.get("type") else None
        tags = set(filters.get("tags") or [])
        max_price = int(filters.get("max_price") or 10_000)
        max_distance = float(filters.get("max_distance") or 99)

        matches = [
            supply
            for supply in self.catalog
            if supply.available
            and (scene is None or scene in supply.scene_fit)
            and (item_type is None or item_type == supply.type)
            and supply.price <= max_price
            and supply.distance_km <= max_distance
        ]
        matches.sort(key=lambda supply: (-len(tags & set(supply.tags)), supply.price, supply.distance_km))
        return ToolResult(
            data=matches,
            event=self._event(
                "meituan.search_merchants",
                filters,
                {"count": len(matches), "top_ids": [item.id for item in matches[:3]]},
                started,
            ),
        )

    def check_availability(self, merchant_id: str, time_window: str, party_size: int) -> ToolResult:
        started = time.perf_counter()
        supply = self._get_supply(merchant_id)
        remaining = max(0, 12 - party_size)
        available = supply is not None and remaining > 0
        data = {
            "merchant_id": merchant_id,
            "available": available,
            "remaining_capacity": remaining,
            "hold_minutes": 15,
            "time_window": time_window,
        }
        return ToolResult(
            data=data,
            event=self._event("meituan.check_availability", {"merchant_id": merchant_id}, data, started),
        )

    def merchant_profile(self, merchant_id: str, merchant_name: str | None = None) -> ToolResult:
        started = time.perf_counter()
        supply = self._get_supply(merchant_id)
        name = merchant_name or (supply.name if supply else merchant_id)
        seed = sum(ord(char) for char in str(merchant_id))
        rating = round(4.1 + (seed % 8) / 10, 1)
        review_count = 80 + seed % 900
        tags = list((supply.tags if supply else [])[:4])
        intro = f"{name} mock 商户介绍：适合主题局候选，真实营业、评价和库存需接入授权美团接口后确认。"
        review_summary = f"mock 用户评价摘要：氛围 {rating}/5，适合聊天/聚会；高峰期建议提前确认座位。"
        data = {
            "merchant_id": merchant_id,
            "merchant_name": name,
            "rating": rating,
            "review_count": review_count,
            "intro": intro,
            "review_summary": review_summary,
            "tags": tags,
            "data_confidence": "mock",
        }
        return ToolResult(
            data=data,
            event=self._event("meituan.merchant_profile", {"merchant_id": merchant_id}, data, started),
        )

    def create_booking_hold(self, items: list[dict[str, object]]) -> ToolResult:
        started = time.perf_counter()
        hold_id = f"hold_{uuid4().hex[:10]}"
        confirm_token = f"confirm_{uuid4().hex[:16]}"
        data = {
            "hold_id": hold_id,
            "confirm_token": confirm_token,
            "status": "pending_user_confirmation",
            "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(timespec="seconds"),
            "items": items,
        }
        return ToolResult(
            data=data,
            event=self._event("meituan.create_booking_hold", {"item_count": len(items)}, data, started),
        )

    def create_aa_draft(self, total: int, party_size: int, mode: str) -> ToolResult:
        started = time.perf_counter()
        data = {
            "aa_id": f"aa_{uuid4().hex[:10]}",
            "total": total,
            "party_size": party_size,
            "per_person": int(round(total / max(1, party_size))),
            "mode": mode,
            "status": "draft",
        }
        return ToolResult(
            data=data,
            event=self._event("meituan.create_aa_draft", {"total": total, "party_size": party_size, "mode": mode}, data, started),
        )

    def confirm_booking(
        self,
        hold_id: str,
        confirm_token: str,
        items: list[dict[str, object]],
    ) -> ToolResult:
        started = time.perf_counter()
        if not hold_id or not confirm_token.startswith("confirm_"):
            data = {"status": "blocked", "reason": "missing_or_invalid_confirm_token"}
            return ToolResult(
                data=data,
                event=self._event("meituan.confirm_booking", {"hold_id": hold_id}, data, started, status="blocked"),
            )

        data = {
            "status": "confirmed",
            "order_ids": [f"order_{uuid4().hex[:8]}" for _ in items],
            "reservation_ids": [f"resv_{uuid4().hex[:8]}" for item in items if item.get("type") in {"activity", "dining", "relax", "nightlife"}],
            "ticket_ids": [f"ticket_{uuid4().hex[:8]}" for item in items if "ticket" in item.get("booking_modes", [])],
            "hotel_order_ids": [f"hotel_{uuid4().hex[:8]}" for item in items if item.get("type") == "hotel"],
            "delivery_order_ids": [f"delivery_{uuid4().hex[:8]}" for item in items if item.get("type") == "gift"],
        }
        return ToolResult(
            data=data,
            event=self._event("meituan.confirm_booking", {"hold_id": hold_id, "item_count": len(items)}, data, started),
        )

    def _get_supply(self, merchant_id: str) -> MerchantSupply | None:
        return next((supply for supply in self.catalog if supply.id == merchant_id), None)

    def _event(
        self,
        name: str,
        input_summary: dict[str, object],
        output_summary: dict[str, object],
        started: float,
        status: str = "ok",
        error: str | None = None,
    ) -> ToolEvent:
        return ToolEvent(
            name=name,
            input_summary=input_summary,
            output_summary=output_summary,
            status=status,
            duration_ms=int((time.perf_counter() - started) * 1000),
            error=error,
        )
