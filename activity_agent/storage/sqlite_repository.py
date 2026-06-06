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
        aa_draft=dict(data.get("aa_draft", {})),
        tool_events=[_tool_event_from_dict(item) for item in data.get("tool_events", [])],
    )
