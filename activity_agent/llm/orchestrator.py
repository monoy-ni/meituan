from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from activity_agent.domain.models import ToolEvent
from activity_agent.llm.client import LLMClient


SYSTEM_PROMPT = """你是本地活动规划 Agent 的结构化理解层。
只输出 JSON，不输出 Markdown。不要编造商户，不要确认支付，不要下单。
可输出字段：scene, intent, time_window, location_anchor, budget_per_person, party_size,
mood_tags, relationship_stage, relationship_goal, hard_constraints, feedback_summary, adjustment_summary。
hard_constraints 可包含 no_alcohol, indoor_only, cheaper, photo_friendly, quiet, hotel_wanted, gift_wanted, partial_allowed。
"""


@dataclass(frozen=True)
class LLMUnderstanding:
    data: dict[str, Any]
    degraded: bool
    event: ToolEvent


class LLMOrchestrator:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def understand(self, text: str, history: list[dict[str, str]] | None = None) -> LLMUnderstanding:
        started = time.perf_counter()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in (history or [])[-6:]:
            messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": text})

        try:
            raw = self.client.complete(messages)
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("LLM JSON root must be an object.")
            event = ToolEvent(
                name="llm.understand",
                input_summary={"text": text[:120]},
                output_summary={"keys": sorted(data.keys())},
                status="ok",
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
            return LLMUnderstanding(data=data, degraded=False, event=event)
        except Exception as exc:
            event = ToolEvent(
                name="llm.understand",
                input_summary={"text": text[:120]},
                output_summary={"fallback": "rule_parser"},
                status="error",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
            return LLMUnderstanding(data={}, degraded=True, event=event)

