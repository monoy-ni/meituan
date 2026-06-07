from __future__ import annotations

import os
import sys
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from activity_agent import ActivityPlanningAgent
from activity_agent.data.hangzhou_catalog import HANGZHOU_DEMO_VERSION
from activity_agent.domain import AgentResponse, BookingConfirmation, BookingDraft, PlanOption, TimelineItem, UserRequest


BACKEND_VERSION = "1.5.0"
FRONTEND_TARGET_VERSION = "0.6.0"

app = FastAPI(title="杭州本地一日主题局 Agent API", version=BACKEND_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ActivityPlanningAgent.from_env()
sessions: dict[str, Any] = {}


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class GuidedChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    scene_hint: Literal["friends", "couple"] | None = None


class SelectOptionRequest(BaseModel):
    session_id: str
    option_id: str


class BookingConfirmRequest(BaseModel):
    session_id: str
    draft_id: str
    confirm: bool = True


class GenerateItineraryRequest(BaseModel):
    session_id: str | None = None
    city: str = "hangzhou"
    location: str | None = None
    date: str | None = None
    duration: str | None = None
    theme_id: str | None = None
    message: str | None = None
    budget_per_person: int | None = Field(default=None, ge=0)
    party_size: int | None = Field(default=None, ge=1)
    experience_tags: list[str] = Field(default_factory=list)
    crowd: str | None = None
    effort_preference: str | None = None
    weather: str | None = None
    search_radius_km: float | None = Field(default=None, ge=0)
    route_limit_km: float | None = Field(default=None, ge=0)
    route_limit_minutes: int | None = Field(default=None, ge=0)


class RefreshItineraryRequest(BaseModel):
    session_id: str


class ProviderSyncRequest(BaseModel):
    city: str = "hangzhou"
    keywords: list[str] = Field(default_factory=list)
    area: str | None = None


def _get_or_create_session_id(session_id: str | None = None) -> str:
    if not session_id:
        session = agent.start_session()
        sessions[session.id] = session
        return session.id
    try:
        agent._ensure_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return session_id


def _request_payload(request: UserRequest | None) -> dict[str, Any] | None:
    if request is None:
        return None
    return {
        "scene": request.scene.value,
        "time_window": request.time_window,
        "location_anchor": request.location_anchor,
        "budget_per_person": request.budget_per_person,
        "party_size": request.party_size,
        "mood_tags": request.mood_tags,
        "relationship_stage": request.relationship_stage,
        "relationship_goal": request.relationship_goal,
        "hard_constraints": request.hard_constraints,
        "journey_duration": request.journey_duration,
        "experience_tags": request.experience_tags,
        "planning_effort": request.planning_effort,
        "travel_radius_km": request.travel_radius_km,
        "weather_sensitive": request.weather_sensitive,
        "origin_name": request.origin_name,
        "origin_address": request.origin_address,
        "origin_amap_url": request.origin_amap_url,
        "origin_longitude": request.origin_longitude,
        "origin_latitude": request.origin_latitude,
        "search_radius_km": request.search_radius_km,
        "route_limit_km": request.route_limit_km,
        "route_limit_minutes": request.route_limit_minutes,
    }


def _timeline_item_payload(item: TimelineItem) -> dict[str, Any]:
    return {
        "type": item.type.value,
        "merchant_id": item.merchant_id,
        "merchant_name": item.merchant_name,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "booking_required": item.booking_required,
        "price_estimate": item.price_estimate,
        "why_this_fits": item.why_this_fits,
        "booking_modes": item.booking_modes,
        "area_cluster": item.area_cluster,
        "checkin_hint": item.checkin_hint,
        "transport_hint": item.transport_hint,
        "data_confidence": item.data_confidence,
        "address": item.address,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "matched_keyword": item.matched_keyword,
        "matched_keywords": item.matched_keywords,
        "merchant_profile": item.merchant_profile,
    }


def _option_payload(option: PlanOption) -> dict[str, Any]:
    return {
        "id": option.id,
        "theme_name": option.theme_name,
        "emotional_hook": option.emotional_hook,
        "route_story": option.route_story,
        "estimated_cost_per_person": option.estimated_cost_per_person,
        "total_distance": option.total_distance,
        "timeline_items": [_timeline_item_payload(item) for item in option.timeline_items],
        "booking_readiness": option.booking_readiness.value,
        "replaceable_slots": option.replaceable_slots,
        "risk_notes": option.risk_notes,
        "actions": option.actions,
        "add_ons": option.add_ons,
        "invite_copy": option.invite_copy,
        "dating_tips": option.dating_tips,
        "gain_points": option.gain_points,
        "fallbacks": option.fallbacks,
        "checkin_points": option.checkin_points,
        "effort_level": option.effort_level,
        "transport_summary": option.transport_summary,
        "data_confidence": option.data_confidence,
        "search_keywords": option.search_keywords,
        "route_plan": option.route_plan,
    }


def _tool_event_payload(event: Any) -> dict[str, Any]:
    if isinstance(event, dict):
        return event
    return {
        "name": event.name,
        "input_summary": event.input_summary,
        "output_summary": event.output_summary,
        "status": event.status,
        "duration_ms": event.duration_ms,
        "error": event.error,
    }


def _response_payload(response: AgentResponse, conversation: dict[str, object] | None = None) -> dict[str, Any]:
    payload = {
        "session_id": response.session_id,
        "message": response.message,
        "intent": response.intent.value if response.intent else None,
        "scene": response.scene.value if response.scene else None,
        "request": _request_payload(response.request),
        "missing_questions": response.missing_questions,
        "assumptions": response.assumptions,
        "options": [_option_payload(option) for option in response.options],
        "share_cards": response.share_cards,
        "tool_events": [_tool_event_payload(event) for event in response.tool_events],
        "degraded": response.degraded,
        "versions": {
            "backend": BACKEND_VERSION,
            "frontend_target": FRONTEND_TARGET_VERSION,
            "seed": HANGZHOU_DEMO_VERSION,
        },
    }
    if conversation is not None:
        payload["conversation"] = conversation
    return payload


def _booking_draft_payload(draft: BookingDraft) -> dict[str, Any]:
    return {
        "draft_id": draft.id,
        "hold_id": draft.hold_id,
        "status": draft.status,
        "pay_mode": draft.pay_mode.value,
        "refund_policy": draft.refund_policy,
        "confirmation_required": draft.confirmation_required,
        "expires_at": draft.expires_at,
        "safety_notice": draft.safety_notice,
        "data_source": draft.data_source,
        "data_confidence": draft.data_confidence,
        "updated_at": draft.updated_at,
        "aa_draft": draft.aa_draft,
        "items": [
            {
                "merchant_id": item.merchant_id,
                "merchant_name": item.merchant_name,
                "type": item.type.value,
                "booking_modes": item.booking_modes,
                "estimated_price_per_person": item.estimated_price_per_person,
                "action": item.action,
                "status": item.status,
            }
            for item in draft.items
        ],
    }


def _booking_confirmation_payload(confirmation: BookingConfirmation) -> dict[str, Any]:
    return {
        "id": confirmation.id,
        "draft_id": confirmation.draft_id,
        "hold_id": confirmation.hold_id,
        "status": confirmation.status.value,
        "message": confirmation.message,
        "order_ids": confirmation.order_ids,
        "reservation_ids": confirmation.reservation_ids,
        "ticket_ids": confirmation.ticket_ids,
        "hotel_order_ids": confirmation.hotel_order_ids,
        "delivery_order_ids": confirmation.delivery_order_ids,
        "tool_events": [_tool_event_payload(event) for event in confirmation.tool_events],
    }


@app.post("/api/sessions")
def create_session() -> dict[str, str]:
    session = agent.start_session()
    sessions[session.id] = session
    return {"session_id": session.id}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/themes")
def list_themes(city: str = "hangzhou") -> dict[str, Any]:
    return {
        "city": city,
        "themes": agent.list_hangzhou_themes(),
        "route_clusters": agent.local_data_provider.list_route_clusters(city),
        "versions": {
            "backend": BACKEND_VERSION,
            "frontend_target": FRONTEND_TARGET_VERSION,
            "seed": HANGZHOU_DEMO_VERSION,
        },
    }


@app.get("/api/featured-itineraries")
def featured_itineraries(
    city: str = "hangzhou",
    duration: str | None = None,
    date: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    session_id = _get_or_create_session_id(session_id)
    text = "杭州 今天不用想 直接安排 老城烟火 西湖 运河 特色美食"
    if duration == "full_day":
        text += " 一整天"
    elif duration == "half_day":
        text += " 半天"
    if date:
        text += f" {date}"
    response = agent.generate_itineraries(session_id=session_id, city=city, duration=duration, message=text)
    return _response_payload(response)


@app.post("/api/itineraries/generate")
def generate_itineraries(request: GenerateItineraryRequest) -> dict[str, Any]:
    session_id = _get_or_create_session_id(request.session_id)
    message = request.message
    if request.date and message:
        message = f"{message}，{request.date}"
    response = agent.generate_itineraries(
        session_id=session_id,
        city=request.city,
        theme_id=request.theme_id,
        message=message,
        budget_per_person=request.budget_per_person,
        duration=request.duration,
        party_size=request.party_size,
        location=request.location,
        experience_tags=request.experience_tags,
        effort_preference=request.effort_preference,
        weather=request.weather,
        search_radius_km=request.search_radius_km,
        route_limit_km=request.route_limit_km,
        route_limit_minutes=request.route_limit_minutes,
    )
    return _response_payload(response)


@app.post("/api/itineraries/{option_id}/refresh")
def refresh_itinerary(option_id: str, request: RefreshItineraryRequest) -> dict[str, Any]:
    try:
        return agent.refresh_itinerary(request.session_id, option_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/providers/sync")
def sync_providers(request: ProviderSyncRequest) -> dict[str, Any]:
    result = agent.sync_provider_data(request.city, keywords=request.keywords, area=request.area)
    return {
        **result,
        "keywords": request.keywords,
        "area": request.area,
        "versions": {
            "backend": BACKEND_VERSION,
            "seed": HANGZHOU_DEMO_VERSION,
        },
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    session_id = _get_or_create_session_id(request.session_id)
    response = agent.chat(session_id, request.message)
    return _response_payload(response)


@app.post("/api/chat/guided")
def guided_chat(request: GuidedChatRequest) -> dict[str, Any]:
    session_id = _get_or_create_session_id(request.session_id)
    response = agent.chat_with_guidance(session_id, request.message, scene_hint=request.scene_hint)
    conversation = agent.get_conversation_payload(session_id, has_options=bool(response.options))
    return _response_payload(response, conversation=conversation)


@app.post("/api/select-option")
def select_option(request: SelectOptionRequest) -> dict[str, Any]:
    try:
        response = agent.select_option(request.session_id, request.option_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _response_payload(response)


@app.post("/api/create-booking-draft")
def create_booking_draft(request: SelectOptionRequest) -> dict[str, Any]:
    try:
        draft = agent.create_booking_draft(request.session_id, request.option_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _booking_draft_payload(draft)


@app.post("/api/confirm-booking")
def confirm_booking(request: BookingConfirmRequest) -> dict[str, Any]:
    try:
        confirmation = agent.confirm_booking(request.session_id, request.draft_id, request.confirm)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _booking_confirmation_payload(confirmation)


@app.get("/api/conversation-state/{session_id}")
def get_conversation_state(session_id: str) -> dict[str, str]:
    state = agent.get_conversation_state(session_id)
    return {"session_id": session_id, "state": state}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting Hangzhou itinerary Agent API on http://{host}:{port}")
    print(f"API 文档: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)
