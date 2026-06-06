from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from activity_agent.domain.models import (
    BookingConfirmation,
    BookingDraft,
    BookingDraftItem,
    ConfirmationStatus,
    PayMode,
    PlanOption,
    Scene,
    TimelineType,
    UserRequest,
)
from activity_agent.providers import CommerceProvider, MockCommerceProvider
from activity_agent.tools.mock_meituan import MockMeituanToolClient


class BookingOrchestrator:
    """Creates semi-automatic booking drafts. It never performs irreversible payment."""

    def __init__(self, tool_client: CommerceProvider | MockMeituanToolClient | None = None) -> None:
        if tool_client is None:
            self.tool_client: CommerceProvider = MockCommerceProvider(MockMeituanToolClient())
        else:
            self.tool_client = tool_client

    def create_draft(self, option: PlanOption, request: UserRequest, pay_mode: PayMode | None = None) -> BookingDraft:
        selected_pay_mode = pay_mode or (PayMode.AA_PREPAY if request.scene == Scene.FRIENDS else PayMode.SINGLE_PAY)
        events = []
        tool_items = []

        items = []
        for item in option.timeline_items:
            availability = self.tool_client.check_availability(item.merchant_id, request.time_window, request.party_size)
            events.append(availability.event)
            availability_data = dict(availability.data)
            status = "pending_user_confirmation" if availability_data.get("available") else "unavailable_replace_needed"
            items.append(
                BookingDraftItem(
                    merchant_id=item.merchant_id,
                    merchant_name=item.merchant_name,
                    type=item.type,
                    booking_modes=item.booking_modes,
                    estimated_price_per_person=item.price_estimate,
                    action=self._action_for(item.type, item.booking_modes),
                    status=status,
                )
            )
            tool_items.append(
                {
                    "merchant_id": item.merchant_id,
                    "merchant_name": item.merchant_name,
                    "type": item.type.value,
                    "booking_modes": item.booking_modes,
                    "estimated_price_per_person": item.price_estimate,
                    "status": status,
                }
            )

        hold = self.tool_client.create_booking_hold(tool_items)
        events.append(hold.event)
        hold_data = dict(hold.data)

        aa_draft = {}
        if selected_pay_mode == PayMode.AA_PREPAY:
            aa = self.tool_client.create_aa_draft(option.estimated_cost_per_person * request.party_size, request.party_size, selected_pay_mode.value)
            events.append(aa.event)
            aa_draft = dict(aa.data)

        return BookingDraft(
            id=f"draft_{uuid4().hex[:12]}",
            hold_id=str(hold_data["hold_id"]),
            confirm_token=str(hold_data["confirm_token"]),
            status=str(hold_data["status"]),
            items=items,
            pay_mode=selected_pay_mode,
            refund_policy="所有订票、酒店、不可退团购和支付动作都必须在用户确认后执行；确认前仅保留草稿和候选库存。",
            confirmation_required=True,
            expires_at=str(hold_data["expires_at"]),
            safety_notice="半自动确认模式：Agent 可以生成待确认订单和 AA 方案，但不会未经授权支付或下不可逆订单。",
            data_source="seed/mock_commerce",
            data_confidence=option.data_confidence,
            updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            aa_draft=aa_draft,
            tool_events=events,
        )

    def confirm_draft(self, draft: BookingDraft, confirm: bool) -> BookingConfirmation:
        if not confirm:
            return BookingConfirmation(
                id=f"bc_{uuid4().hex[:12]}",
                draft_id=draft.id,
                hold_id=draft.hold_id,
                status=ConfirmationStatus.CANCELLED,
                message="用户未确认，未执行预约、出票、酒店或支付动作。",
            )

        tool_items = [
            {
                "merchant_id": item.merchant_id,
                "merchant_name": item.merchant_name,
                "type": item.type.value,
                "booking_modes": item.booking_modes,
                "estimated_price_per_person": item.estimated_price_per_person,
            }
            for item in draft.items
        ]
        result = self.tool_client.confirm_booking(draft.hold_id, draft.confirm_token, tool_items)
        data = dict(result.data)
        status = ConfirmationStatus.CONFIRMED if data.get("status") == "confirmed" else ConfirmationStatus.BLOCKED
        return BookingConfirmation(
            id=f"bc_{uuid4().hex[:12]}",
            draft_id=draft.id,
            hold_id=draft.hold_id,
            status=status,
            order_ids=list(data.get("order_ids", [])),
            reservation_ids=list(data.get("reservation_ids", [])),
            ticket_ids=list(data.get("ticket_ids", [])),
            hotel_order_ids=list(data.get("hotel_order_ids", [])),
            delivery_order_ids=list(data.get("delivery_order_ids", [])),
            message="已生成 mock 确认订单，用于验证 MVP 闭环。" if status == ConfirmationStatus.CONFIRMED else str(data.get("reason", "确认被阻止。")),
            tool_events=[result.event],
        )

    def _action_for(self, item_type: TimelineType, booking_modes: list[str]) -> str:
        if "hotel" in booking_modes or item_type == TimelineType.HOTEL:
            return "生成酒店待确认订单，展示隐私、安全、退款规则"
        if "instant_delivery" in booking_modes or item_type == TimelineType.GIFT:
            return "生成小时达礼物草稿，等待确认配送地址和时间"
        if "ticket" in booking_modes:
            return "锁定票券/团购候选，等待确认购买"
        if "reservation" in booking_modes:
            return "生成订座/预约草稿，等待确认"
        if "queue" in booking_modes:
            return "生成排队取号建议，等待确认"
        return "无需预付，到店后补差价"
