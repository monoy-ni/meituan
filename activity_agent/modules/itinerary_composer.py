from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from activity_agent.domain.models import (
    BookingReadiness,
    MerchantSupply,
    PlanOption,
    Scene,
    Theme,
    ThemeSlot,
    TimelineItem,
    TimelineType,
    UserRequest,
)
from activity_agent.modules.supply_matcher import SupplyMatcher


DEFAULT_ACTIONS = ["我想去", "换个便宜点的", "只参加后半场", "一键预约", "一键 AA", "转发群聊", "生成朋友圈文案"]


class ItineraryComposer:
    """Composes matched supplies into route-like PlanOption objects."""

    def __init__(self, matcher: SupplyMatcher | None = None) -> None:
        self.matcher = matcher or SupplyMatcher()

    def compose(self, themes: list[Theme], request: UserRequest) -> list[PlanOption]:
        return [self._compose_one(theme, request, index + 1) for index, theme in enumerate(themes)]

    def _compose_one(self, theme: Theme, request: UserRequest, index: int) -> PlanOption:
        used_ids: set[str] = set()
        start = self._start_time(request)
        timeline_items: list[TimelineItem] = []

        for slot in theme.slots:
            supply = self.matcher.match_slot(slot, request, used_ids)
            used_ids.add(supply.id)
            end = start + timedelta(minutes=supply.duration_minutes)
            timeline_items.append(self._to_timeline_item(slot.label, supply, start, end))
            start = end + timedelta(minutes=20)

        items = self._with_couple_addons(theme, request, timeline_items, start)
        estimated_cost = sum(item.price_estimate for item in items)
        total_distance = round(sum(self._distance_for(item) for item in items), 1)
        risk_notes = self._risk_notes(request, items, estimated_cost)

        readiness = (
            BookingReadiness.READY
            if all(item.booking_modes for item in items)
            else BookingReadiness.PARTIAL
        )
        if any(item.booking_required for item in items):
            readiness = BookingReadiness.NEEDS_CONFIRMATION

        return PlanOption(
            id=f"{request.scene.value}-{index}-{theme.id}",
            theme_name=theme.name,
            emotional_hook=theme.emotional_hook,
            timeline_items=items,
            estimated_cost_per_person=estimated_cost,
            total_distance=total_distance,
            booking_readiness=readiness,
            replaceable_slots=[item.type.value for item in items],
            risk_notes=risk_notes,
            actions=self._actions_for(request),
            add_ons=theme.add_ons,
            invite_copy=self._invite_copy(theme, request),
            dating_tips=self._dating_tips(theme, request),
            route_story=theme.route_story or theme.emotional_hook,
            gain_points=theme.gain_points,
            fallbacks=theme.fallbacks,
            checkin_points=theme.checkin_points or [item.merchant_name for item in items if item.type == TimelineType.CHECKIN],
            effort_level=theme.effort_level,
            transport_summary=theme.transport_summary or self._transport_summary(items),
            data_confidence=self._data_confidence(items),
        )

    def _to_timeline_item(
        self,
        label: str,
        supply: MerchantSupply,
        start: datetime,
        end: datetime,
    ) -> TimelineItem:
        return TimelineItem(
            type=supply.type,
            merchant_id=supply.id,
            merchant_name=supply.name,
            start_time=start.strftime("%H:%M"),
            end_time=end.strftime("%H:%M"),
            booking_required=any(mode in supply.booking_modes for mode in ["reservation", "ticket", "group_buy", "hotel", "instant_delivery"]),
            price_estimate=supply.price,
            why_this_fits=f"{label}：{supply.why}",
            booking_modes=supply.booking_modes,
            area_cluster=supply.area_cluster,
            checkin_hint=supply.checkin_value,
            transport_hint=supply.transport_hint,
            data_confidence=supply.data_confidence,
            address=supply.address,
            latitude=supply.latitude,
            longitude=supply.longitude,
            matched_keyword=supply.matched_keywords[0] if supply.matched_keywords else "",
            matched_keywords=supply.matched_keywords,
            merchant_profile=supply.merchant_profile,
        )

    def _with_couple_addons(
        self,
        theme: Theme,
        request: UserRequest,
        items: list[TimelineItem],
        start: datetime,
    ) -> list[TimelineItem]:
        if request.scene != Scene.COUPLE:
            return items
        if request.hard_constraints.get("gift_wanted") or request.relationship_stage in {"纪念日", "想制造惊喜"}:
            gift_slot = TimelineType.GIFT
            if not any(item.type == gift_slot for item in items):
                try:
                    supply = self.matcher.match_slot(
                        slot=ThemeSlot(gift_slot, ["小时达", "仪式感", "纪念日"], "用低负担小惊喜补一个表达"),
                        request=request,
                        used_ids={item.merchant_id for item in items},
                    )
                except ValueError:
                    return items
                gift_start = start
                gift_end = start + timedelta(minutes=supply.duration_minutes)
                return [
                    *items,
                    self._to_timeline_item("用低负担小惊喜补一个表达", supply, gift_start, gift_end),
                ]
        return items

    def _risk_notes(self, request: UserRequest, items: list[TimelineItem], estimated_cost: int) -> list[str]:
        notes: list[str] = []
        if estimated_cost > request.budget_per_person:
            notes.append(f"当前预估人均 {estimated_cost} 元，高于预算 {request.budget_per_person} 元，可切换便宜替换项。")
        if request.scene == Scene.COUPLE and request.relationship_stage == "暧昧/追求中":
            notes.append("暧昧/追求中默认不安排酒店、过度私密空间或高压表白。")
        if request.hard_constraints.get("no_alcohol"):
            notes.append("已按不喝酒偏好过滤微醺/酒吧供给。")
        if any(item.type == TimelineType.HOTEL for item in items):
            notes.append("酒店/夜宿必须双方明确接受，并在支付前再次确认隐私、安全和退款规则。")
        if request.weather_sensitive:
            notes.append("天气为 seed 估算，出发前建议刷新确认；已优先安排室内或低天气风险供给。")
        if any(item.data_confidence not in {"realtime", "live", "official"} for item in items):
            notes.append("路线、库存和价格当前为 seed/缓存估算，确认前需刷新。")
        return notes

    def _invite_copy(self, theme: Theme, request: UserRequest) -> str | None:
        if request.scene == Scene.FRIENDS:
            return None
        if request.relationship_stage == "暧昧/追求中":
            return "我看到一个时间不长的手作体验，感觉你应该会喜欢。做完附近有家评价不错的甜品店，周末下午有空的话，要不要一起去试试？"
        if request.relationship_stage == "想修复关系":
            return "这周我们找个不赶路的晚上，先吃点东西、散散步，不急着把所有话一次说完，好吗？"
        return "这个周末我们换一种方式过一下，做点小东西、吃顿好吃的，再慢慢散步，给这周留个只属于我们的晚上。"

    def _dating_tips(self, theme: Theme, request: UserRequest) -> list[str]:
        if request.scene != Scene.COUPLE:
            return []
        tips = ["提前看天气和交通，给迟到留 15 分钟缓冲。", "餐厅优先选安静、不催桌、方便自然聊天的位置。"]
        if request.relationship_stage == "暧昧/追求中":
            tips.extend(["不要一开始安排酒店或过度私密空间。", "结束时用“下次可以一起试试……”铺垫，而不是现场逼问结果。"])
        if request.hard_constraints.get("gift_wanted") or request.relationship_stage in {"纪念日", "想制造惊喜"}:
            tips.append("礼物优先低负担、有细节，可选花束/蛋糕/香薰等即时履约商品。")
        return tips

    def _start_time(self, request: UserRequest) -> datetime:
        if request.journey_duration == "full_day":
            return datetime(2026, 5, 28, 10, 30)
        if request.journey_duration == "half_day" and "18:30" not in request.time_window:
            return datetime(2026, 5, 28, 14, 0)
        if "15:00" in request.time_window:
            hour, minute = 15, 0
        elif "14:00" in request.time_window:
            hour, minute = 14, 0
        else:
            hour, minute = 18, 30
        return datetime(2026, 5, 28, hour, minute)

    def _actions_for(self, request: UserRequest) -> list[str]:
        if "杭州" in request.experience_tags or request.planning_effort == "zero_effort":
            return ["就按这个走", "更近一点", "便宜点", "少走路", "改室内", "加拍照点", "一键预约"]
        return DEFAULT_ACTIONS if request.scene == Scene.FRIENDS else ["确认约会", "换个轻一点的", "加礼物", "一键预约", "生成邀约话术"]

    def _transport_summary(self, items: list[TimelineItem]) -> str:
        clusters = [item.area_cluster for item in items if item.area_cluster]
        if not clusters:
            return "路线为 seed 估算，建议出发前刷新地图。"
        if len(set(clusters)) == 1:
            return "同片区步行串联，通勤压力低。"
        return "包含跨片区移动，建议预留地铁或打车时间。"

    def _data_confidence(self, items: list[TimelineItem]) -> str:
        values = {item.data_confidence for item in items}
        if values <= {"realtime", "live", "official"}:
            return "live" if "live" in values else "realtime"
        if "cache" in values:
            return "cache"
        return "seed"

    def _distance_for(self, item: TimelineItem) -> float:
        for supply in self.matcher.catalog:
            if supply.id == item.merchant_id:
                return supply.distance_km
        return 0.0
