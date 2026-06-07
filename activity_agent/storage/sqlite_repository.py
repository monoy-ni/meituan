from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from activity_agent.domain.models import (
    AfterActionReview,
    BookingConfirmation,
    BookingDraft,
    BookingDraftItem,
    BookingReadiness,
    ConfirmationStatus,
    FeedbackStatus,
    InviteFeedback,
    Intent,
    MerchantSupply,
    PayMode,
    PlanOption,
    PlanningResult,
    RouteResult,
    Scene,
    Session,
    TimelineItem,
    TimelineType,
    ToolEvent,
    UserRequest,
)


SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return str(value)


def _to_json(value: Any) -> str:
    return json.dumps(value, default=_json_default, ensure_ascii=False)


def _from_json(value: str) -> dict[str, Any]:
    return json.loads(value)


class SQLiteRepository:
    """Small JSON-over-SQLite state store for the SDK MVP."""

    def __init__(self, path: str = "./activity_agent.sqlite3") -> None:
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection: sqlite3.Connection | None = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def create_session(self, user_id: str | None = None) -> Session:
        session = Session(id=f"sess_{uuid4().hex[:12]}", user_id=user_id, created_at=_now(), updated_at=_now())
        self.connection.execute(
            "INSERT INTO sessions (id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session.id, session.user_id, session.created_at, session.updated_at),
        )
        self.connection.commit()
        return session

    def get_session(self, session_id: str) -> Session | None:
        row = self.connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        return Session(id=row["id"], user_id=row["user_id"], created_at=row["created_at"], updated_at=row["updated_at"])

    def touch_session(self, session_id: str) -> None:
        self.connection.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (_now(), session_id))
        self.connection.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.connection.execute(
            "INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (f"msg_{uuid4().hex[:12]}", session_id, role, content, _now()),
        )
        self.touch_session(session_id)

    def list_messages(self, session_id: str, limit: int = 20) -> list[dict[str, str]]:
        rows = self.connection.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def save_planning_result(self, session_id: str, result: PlanningResult, share_cards: list[str]) -> str:
        planning_id = f"plan_{uuid4().hex[:12]}"
        payload = {
            "schema_version": SCHEMA_VERSION,
            "route": asdict(result.route),
            "request": asdict(result.request),
            "missing_questions": result.missing_questions,
            "assumptions": result.assumptions,
            "options": [asdict(option) for option in result.options],
            "share_cards": share_cards,
        }
        self.connection.execute(
            "INSERT INTO planning_results (id, session_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (planning_id, session_id, _to_json(payload), _now()),
        )
        self.touch_session(session_id)
        return planning_id

    def get_latest_planning(self, session_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload_json FROM planning_results WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        payload = _from_json(row["payload_json"])
        return {
            "route": _route_from_dict(payload["route"]),
            "request": _request_from_dict(payload["request"]),
            "missing_questions": payload.get("missing_questions", []),
            "assumptions": payload.get("assumptions", []),
            "options": [_plan_option_from_dict(item) for item in payload.get("options", [])],
            "share_cards": payload.get("share_cards", []),
        }

    def save_selected_option(self, session_id: str, option: PlanOption, request: UserRequest) -> str:
        selected_id = f"sel_{uuid4().hex[:12]}"
        payload = {"option": asdict(option), "request": asdict(request), "schema_version": SCHEMA_VERSION}
        self.connection.execute(
            "INSERT INTO selected_options (id, session_id, option_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (selected_id, session_id, option.id, _to_json(payload), _now()),
        )
        self.touch_session(session_id)
        return selected_id

    def get_selected_option(self, session_id: str) -> tuple[PlanOption, UserRequest] | None:
        row = self.connection.execute(
            "SELECT payload_json FROM selected_options WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        payload = _from_json(row["payload_json"])
        return _plan_option_from_dict(payload["option"]), _request_from_dict(payload["request"])

    def save_feedback(self, session_id: str, feedback: list[InviteFeedback]) -> str:
        feedback_id = f"fb_{uuid4().hex[:12]}"
        payload = {"schema_version": SCHEMA_VERSION, "feedback": [asdict(item) for item in feedback]}
        self.connection.execute(
            "INSERT INTO invite_feedback (id, session_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (feedback_id, session_id, _to_json(payload), _now()),
        )
        self.touch_session(session_id)
        return feedback_id

    def save_booking_draft(self, session_id: str, draft: BookingDraft) -> None:
        self.connection.execute(
            "INSERT INTO booking_drafts (id, session_id, draft_json, created_at) VALUES (?, ?, ?, ?)",
            (draft.id, session_id, _to_json(asdict(draft)), _now()),
        )
        self.touch_session(session_id)

    def get_booking_draft(self, session_id: str, draft_id: str) -> BookingDraft | None:
        row = self.connection.execute(
            "SELECT draft_json FROM booking_drafts WHERE session_id = ? AND id = ?",
            (session_id, draft_id),
        ).fetchone()
        return _booking_draft_from_dict(_from_json(row["draft_json"])) if row else None

    def save_booking_confirmation(self, session_id: str, confirmation: BookingConfirmation) -> None:
        self.connection.execute(
            "INSERT INTO booking_confirmations (id, session_id, confirmation_json, created_at) VALUES (?, ?, ?, ?)",
            (confirmation.id, session_id, _to_json(asdict(confirmation)), _now()),
        )
        self.touch_session(session_id)

    def save_review(self, session_id: str, review: AfterActionReview) -> None:
        self.connection.execute(
            "INSERT INTO after_action_reviews (id, session_id, review_json, created_at) VALUES (?, ?, ?, ?)",
            (f"review_{uuid4().hex[:12]}", session_id, _to_json(asdict(review)), _now()),
        )
        self.touch_session(session_id)

    def seed_local_catalog(
        self,
        supplies: list[Any],
        route_clusters: list[dict[str, Any]],
        theme_templates: list[dict[str, Any]],
    ) -> None:
        for supply in supplies:
            payload = asdict(supply) if is_dataclass(supply) else dict(supply)
            self.connection.execute(
                """
                INSERT OR REPLACE INTO places (
                    id, city, area_cluster, type, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload.get("city", "hangzhou"),
                    payload.get("area_cluster", ""),
                    payload.get("type", ""),
                    _to_json(payload),
                    _now(),
                ),
            )
            self.connection.execute("DELETE FROM place_tags WHERE place_id = ?", (payload["id"],))
            for tag in [*payload.get("tags", []), *payload.get("local_flavor_tags", [])]:
                self.connection.execute(
                    "INSERT INTO place_tags (place_id, tag) VALUES (?, ?)",
                    (payload["id"], tag),
                )

        for cluster in route_clusters:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO route_clusters (
                    id, city, name, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    cluster["id"],
                    cluster.get("city", "hangzhou"),
                    cluster.get("name", cluster["id"]),
                    _to_json(cluster),
                    _now(),
                ),
            )

        for template in theme_templates:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO theme_templates (
                    id, city, name, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    template["id"],
                    template.get("city", "hangzhou"),
                    template.get("name", template["id"]),
                    _to_json(template),
                    _now(),
                ),
            )

        self.connection.execute(
            "INSERT OR REPLACE INTO source_records (id, source, status, payload_json, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                "source_seed_hangzhou_v1_4_0",
                "seed",
                "ok",
                _to_json({"city": "hangzhou", "places": len(supplies), "templates": len(theme_templates)}),
                _now(),
            ),
        )
        self.connection.commit()

    def upsert_supplies(self, supplies: list[Any], source: str, status: str = "ok") -> None:
        for supply in supplies:
            payload = asdict(supply) if is_dataclass(supply) else dict(supply)
            self.connection.execute(
                """
                INSERT OR REPLACE INTO places (
                    id, city, area_cluster, type, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload.get("city", "hangzhou"),
                    payload.get("area_cluster", ""),
                    payload.get("type", ""),
                    _to_json(payload),
                    _now(),
                ),
            )
            self.connection.execute("DELETE FROM place_tags WHERE place_id = ?", (payload["id"],))
            for tag in [*payload.get("tags", []), *payload.get("local_flavor_tags", [])]:
                self.connection.execute(
                    "INSERT INTO place_tags (place_id, tag) VALUES (?, ?)",
                    (payload["id"], tag),
                )

        self.connection.execute(
            "INSERT OR REPLACE INTO source_records (id, source, status, payload_json, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                f"source_{source}",
                source,
                status,
                _to_json({"places": len(supplies)}),
                _now(),
            ),
        )
        self.connection.commit()

    def list_local_supplies(self, city: str = "hangzhou") -> list[MerchantSupply]:
        rows = self.connection.execute(
            "SELECT payload_json FROM places WHERE city = ? ORDER BY area_cluster, type, id",
            (city,),
        ).fetchall()
        return [_merchant_supply_from_dict(_from_json(row["payload_json"])) for row in rows]

    def list_route_clusters(self, city: str = "hangzhou") -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload_json FROM route_clusters WHERE city = ? ORDER BY name",
            (city,),
        ).fetchall()
        return [_from_json(row["payload_json"]) for row in rows]

    def list_theme_templates(self, city: str = "hangzhou") -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload_json FROM theme_templates WHERE city = ? ORDER BY name",
            (city,),
        ).fetchall()
        return [_from_json(row["payload_json"]) for row in rows]

    def get_api_cache(self, provider: str, query_hash: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload_json FROM api_cache WHERE provider = ? AND query_hash = ?",
            (provider, query_hash),
        ).fetchone()
        return _from_json(row["payload_json"]) if row else None

    def save_api_cache(self, provider: str, query_hash: str, status: str, ttl_seconds: int, payload: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO api_cache (
                provider, query_hash, status, ttl_seconds, payload_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (provider, query_hash, status, ttl_seconds, _to_json(payload), _now()),
        )
        self.connection.commit()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS planning_results (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS selected_options (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                option_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS booking_drafts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                draft_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS booking_confirmations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                confirmation_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS invite_feedback (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS after_action_reviews (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                review_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS places (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                area_cluster TEXT NOT NULL,
                type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS place_tags (
                place_id TEXT NOT NULL,
                tag TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS route_clusters (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS theme_templates (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS api_cache (
                provider TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (provider, query_hash)
            );
            CREATE TABLE IF NOT EXISTS source_records (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()


def _route_from_dict(data: dict[str, Any]) -> RouteResult:
    return RouteResult(intent=Intent(data["intent"]), scene=Scene(data["scene"]), confidence=data["confidence"], signals=data.get("signals", []))


def _request_from_dict(data: dict[str, Any]) -> UserRequest:
    return UserRequest(
        scene=Scene(data["scene"]),
        time_window=data["time_window"],
        location_anchor=data["location_anchor"],
        budget_per_person=int(data["budget_per_person"]),
        party_size=int(data["party_size"]),
        mood_tags=list(data.get("mood_tags", [])),
        relationship_stage=data.get("relationship_stage"),
        relationship_goal=data.get("relationship_goal"),
        hard_constraints=dict(data.get("hard_constraints", {})),
        journey_duration=data.get("journey_duration", "evening"),
        experience_tags=list(data.get("experience_tags", [])),
        planning_effort=data.get("planning_effort", "guided"),
        travel_radius_km=float(data.get("travel_radius_km", 3.0)),
        weather_sensitive=bool(data.get("weather_sensitive", False)),
        origin_name=data.get("origin_name", "奥映世纪轩"),
        origin_address=data.get("origin_address", "民祥路与平澜路交汇处(地铁6号线丰北站C出口)"),
        origin_amap_url=data.get("origin_amap_url", "https://surl.amap.com/4sRsg3c1oa7b"),
        origin_longitude=data.get("origin_longitude", 120.2425),
        origin_latitude=data.get("origin_latitude", 30.2426),
        search_radius_km=float(data.get("search_radius_km", 5.0)),
        route_limit_km=float(data.get("route_limit_km", 6.0)),
        route_limit_minutes=int(data.get("route_limit_minutes", 45)),
    )


def _merchant_supply_from_dict(data: dict[str, Any]) -> MerchantSupply:
    return MerchantSupply(
        id=data["id"],
        name=data["name"],
        type=TimelineType(data["type"]),
        price=int(data["price"]),
        duration_minutes=int(data["duration_minutes"]),
        distance_km=float(data["distance_km"]),
        district=data["district"],
        tags=list(data.get("tags", [])),
        scene_fit=[Scene(item) for item in data.get("scene_fit", [])],
        booking_modes=list(data.get("booking_modes", [])),
        available=bool(data["available"]),
        why=data["why"],
        source=data.get("source", "seed"),
        source_id=data.get("source_id", ""),
        city=data.get("city", "hangzhou"),
        address=data.get("address", ""),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        area_cluster=data.get("area_cluster", ""),
        open_dayparts=list(data.get("open_dayparts", [])),
        weather_fit=list(data.get("weather_fit", [])),
        checkin_value=data.get("checkin_value", ""),
        local_flavor_tags=list(data.get("local_flavor_tags", [])),
        transport_hint=data.get("transport_hint", ""),
        data_confidence=data.get("data_confidence", "seed"),
        matched_keywords=list(data.get("matched_keywords", [])),
        merchant_profile=dict(data.get("merchant_profile", {})),
    )


def _timeline_item_from_dict(data: dict[str, Any]) -> TimelineItem:
    return TimelineItem(
        type=TimelineType(data["type"]),
        merchant_id=data["merchant_id"],
        merchant_name=data["merchant_name"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        booking_required=bool(data["booking_required"]),
        price_estimate=int(data["price_estimate"]),
        why_this_fits=data["why_this_fits"],
        booking_modes=list(data.get("booking_modes", [])),
        area_cluster=data.get("area_cluster", ""),
        checkin_hint=data.get("checkin_hint", ""),
        transport_hint=data.get("transport_hint", ""),
        data_confidence=data.get("data_confidence", "seed"),
        address=data.get("address", ""),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        matched_keyword=data.get("matched_keyword", ""),
        matched_keywords=list(data.get("matched_keywords", [])),
        merchant_profile=dict(data.get("merchant_profile", {})),
    )


def _plan_option_from_dict(data: dict[str, Any]) -> PlanOption:
    return PlanOption(
        id=data["id"],
        theme_name=data["theme_name"],
        emotional_hook=data["emotional_hook"],
        timeline_items=[_timeline_item_from_dict(item) for item in data.get("timeline_items", [])],
        estimated_cost_per_person=int(data["estimated_cost_per_person"]),
        total_distance=float(data["total_distance"]),
        booking_readiness=BookingReadiness(data["booking_readiness"]),
        replaceable_slots=list(data.get("replaceable_slots", [])),
        risk_notes=list(data.get("risk_notes", [])),
        actions=list(data.get("actions", [])),
        add_ons=list(data.get("add_ons", [])),
        invite_copy=data.get("invite_copy"),
        dating_tips=list(data.get("dating_tips", [])),
        route_story=data.get("route_story", ""),
        gain_points=list(data.get("gain_points", [])),
        fallbacks=list(data.get("fallbacks", [])),
        checkin_points=list(data.get("checkin_points", [])),
        effort_level=data.get("effort_level", "中"),
        transport_summary=data.get("transport_summary", ""),
        data_confidence=data.get("data_confidence", "seed"),
        search_keywords=list(data.get("search_keywords", [])),
        route_plan=dict(data.get("route_plan", {})),
        experience_card=dict(data.get("experience_card", {})),
    )


def _tool_event_from_dict(data: dict[str, Any]) -> ToolEvent:
    return ToolEvent(
        name=data["name"],
        input_summary=dict(data.get("input_summary", {})),
        output_summary=dict(data.get("output_summary", {})),
        status=data["status"],
        duration_ms=int(data["duration_ms"]),
        error=data.get("error"),
    )


def _booking_draft_item_from_dict(data: dict[str, Any]) -> BookingDraftItem:
    return BookingDraftItem(
        merchant_id=data["merchant_id"],
        merchant_name=data["merchant_name"],
        type=TimelineType(data["type"]),
        booking_modes=list(data.get("booking_modes", [])),
        estimated_price_per_person=int(data["estimated_price_per_person"]),
        action=data["action"],
        status=data["status"],
    )


def _booking_draft_from_dict(data: dict[str, Any]) -> BookingDraft:
    return BookingDraft(
        items=[_booking_draft_item_from_dict(item) for item in data.get("items", [])],
        pay_mode=PayMode(data["pay_mode"]),
        refund_policy=data["refund_policy"],
        confirmation_required=bool(data["confirmation_required"]),
        expires_at=data["expires_at"],
        safety_notice=data["safety_notice"],
        id=data.get("id", ""),
        hold_id=data.get("hold_id", ""),
        confirm_token=data.get("confirm_token", ""),
        status=data.get("status", "pending_user_confirmation"),
        data_source=data.get("data_source", "seed"),
        data_confidence=data.get("data_confidence", "seed"),
        updated_at=data.get("updated_at", ""),
        aa_draft=dict(data.get("aa_draft", {})),
        tool_events=[_tool_event_from_dict(item) for item in data.get("tool_events", [])],
    )
