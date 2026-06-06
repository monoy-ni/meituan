from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Scene(StrEnum):
    FRIENDS = "friends"
    COUPLE = "couple"


class Intent(StrEnum):
    PLAN = "plan"
    ADJUST = "adjust"
    FEEDBACK = "feedback"
    BOOKING = "booking"
    REVIEW = "review"


class TimelineType(StrEnum):
    ACTIVITY = "activity"
    DINING = "dining"
    CHECKIN = "checkin"
    RELAX = "relax"
    NIGHTLIFE = "nightlife"
    HOTEL = "hotel"
    GIFT = "gift"
    TRANSPORT = "transport"


class PayMode(StrEnum):
    SINGLE_PAY = "single_pay"
    AA_PREPAY = "aa_prepay"
    PAY_LATER = "pay_later"


class FeedbackStatus(StrEnum):
    JOIN = "join"
    REJECT = "reject"
    LATE = "late"
    PARTIAL = "partial"


class BookingReadiness(StrEnum):
    READY = "ready"
    NEEDS_CONFIRMATION = "needs_confirmation"
    PARTIAL = "partial"


class ConfirmationStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Session:
    id: str
    user_id: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ToolEvent:
    name: str
    input_summary: dict[str, Any]
    output_summary: dict[str, Any]
    status: str
    duration_ms: int
    error: str | None = None


@dataclass(frozen=True)
class RouteResult:
    intent: Intent
    scene: Scene
    confidence: float
    signals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UserRequest:
    scene: Scene
    time_window: str
    location_anchor: str
    budget_per_person: int
    party_size: int
    mood_tags: list[str] = field(default_factory=list)
    relationship_stage: str | None = None
    relationship_goal: str | None = None
    hard_constraints: dict[str, Any] = field(default_factory=dict)
    journey_duration: str = "evening"
    experience_tags: list[str] = field(default_factory=list)
    planning_effort: str = "guided"
    travel_radius_km: float = 3.0
    weather_sensitive: bool = False


@dataclass(frozen=True)
class MerchantSupply:
    id: str
    name: str
    type: TimelineType
    price: int
    duration_minutes: int
    distance_km: float
    district: str
    tags: list[str]
    scene_fit: list[Scene]
    booking_modes: list[str]
    available: bool
    why: str
    source: str = "seed"
    source_id: str = ""
    city: str = "hangzhou"
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    area_cluster: str = ""
    open_dayparts: list[str] = field(default_factory=list)
    weather_fit: list[str] = field(default_factory=list)
    checkin_value: str = ""
    local_flavor_tags: list[str] = field(default_factory=list)
    transport_hint: str = ""
    data_confidence: str = "seed"


@dataclass(frozen=True)
class ThemeSlot:
    type: TimelineType
    desired_tags: list[str]
    label: str
    area_clusters: list[str] = field(default_factory=list)
    optional: bool = False


@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    emotional_hook: str
    slots: list[ThemeSlot]
    add_ons: list[str]
    trigger_tags: list[str] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    city: str = "hangzhou"
    journey_duration: str = "evening"
    route_story: str = ""
    experience_tags: list[str] = field(default_factory=list)
    effort_level: str = "中"
    transport_summary: str = ""
    gain_points: list[str] = field(default_factory=list)
    checkin_points: list[str] = field(default_factory=list)
    fallbacks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TimelineItem:
    type: TimelineType
    merchant_id: str
    merchant_name: str
    start_time: str
    end_time: str
    booking_required: bool
    price_estimate: int
    why_this_fits: str
    booking_modes: list[str]
    area_cluster: str = ""
    checkin_hint: str = ""
    transport_hint: str = ""
    data_confidence: str = "seed"


@dataclass(frozen=True)
class PlanOption:
    id: str
    theme_name: str
    emotional_hook: str
    timeline_items: list[TimelineItem]
    estimated_cost_per_person: int
    total_distance: float
    booking_readiness: BookingReadiness
    replaceable_slots: list[str]
    risk_notes: list[str]
    actions: list[str]
    add_ons: list[str]
    invite_copy: str | None = None
    dating_tips: list[str] = field(default_factory=list)
    route_story: str = ""
    gain_points: list[str] = field(default_factory=list)
    fallbacks: list[str] = field(default_factory=list)
    checkin_points: list[str] = field(default_factory=list)
    effort_level: str = "中"
    transport_summary: str = ""
    data_confidence: str = "seed"


@dataclass(frozen=True)
class InviteFeedback:
    participant_id: str
    status: FeedbackStatus
    budget_feedback: int | None = None
    time_feedback: str | None = None
    preference_tags: list[str] = field(default_factory=list)
    dietary_or_boundary_constraints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BookingDraftItem:
    merchant_id: str
    merchant_name: str
    type: TimelineType
    booking_modes: list[str]
    estimated_price_per_person: int
    action: str
    status: str


@dataclass(frozen=True)
class BookingDraft:
    items: list[BookingDraftItem]
    pay_mode: PayMode
    refund_policy: str
    confirmation_required: bool
    expires_at: str
    safety_notice: str
    id: str = ""
    hold_id: str = ""
    confirm_token: str = ""
    status: str = "pending_user_confirmation"
    data_source: str = "seed"
    data_confidence: str = "seed"
    updated_at: str = ""
    aa_draft: dict[str, Any] = field(default_factory=dict)
    tool_events: list[ToolEvent] = field(default_factory=list)


@dataclass(frozen=True)
class BookingConfirmation:
    id: str
    draft_id: str
    hold_id: str
    status: ConfirmationStatus
    order_ids: list[str] = field(default_factory=list)
    reservation_ids: list[str] = field(default_factory=list)
    ticket_ids: list[str] = field(default_factory=list)
    hotel_order_ids: list[str] = field(default_factory=list)
    delivery_order_ids: list[str] = field(default_factory=list)
    message: str = ""
    tool_events: list[ToolEvent] = field(default_factory=list)


@dataclass(frozen=True)
class AfterActionReview:
    actual_cost_per_person: int
    attendance: int
    ratings: dict[str, float]
    best_segment: str
    complaints: list[str]
    updated_preferences: list[str]
    next_recommendations: list[str]
    share_copy: str


@dataclass(frozen=True)
class PlanningResult:
    route: RouteResult
    request: UserRequest
    missing_questions: list[str]
    assumptions: list[str]
    options: list[PlanOption]


@dataclass(frozen=True)
class AgentResponse:
    session_id: str
    intent: Intent
    scene: Scene
    message: str
    request: UserRequest | None = None
    options: list[PlanOption] = field(default_factory=list)
    share_cards: list[str] = field(default_factory=list)
    booking_draft: BookingDraft | None = None
    booking_confirmation: BookingConfirmation | None = None
    review: AfterActionReview | None = None
    missing_questions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    tool_events: list[ToolEvent] = field(default_factory=list)
    degraded: bool = False
