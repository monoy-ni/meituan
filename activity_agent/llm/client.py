from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from activity_agent.config import LLMSettings


class LLMError(RuntimeError):
    pass


class LLMConfigurationError(LLMError):
    pass


class LLMClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        ...


@dataclass
class OpenAICompatibleLLMClient:
    settings: LLMSettings

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.settings.api_key:
            raise LLMConfigurationError("ACTIVITY_AGENT_LLM_API_KEY is required for OpenAI-compatible LLM calls.")

        url = f"{self.settings.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LLMError("LLM response was not valid JSON.") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM response did not contain choices[0].message.content.") from exc


class MockLLMClient:
    """Offline client that returns deterministic structured extraction JSON."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        user_text = messages[-1]["content"] if messages else ""
        data: dict[str, object] = {
            "scene": "couple" if any(word in user_text for word in ["约会", "TA", "ta", "女朋友", "男朋友", "纪念日", "酒店"]) else "friends",
            "mood_tags": [],
            "hard_constraints": {},
        }
        if any(word in user_text for word in ["便宜", "预算太高", "省钱"]):
            data["mood_tags"] = ["省钱"]
            data["hard_constraints"] = {"cheaper": True}
        if "不喝酒" in user_text:
            data["hard_constraints"] = {**dict(data["hard_constraints"]), "no_alcohol": True}
        if "室内" in user_text:
            data["hard_constraints"] = {**dict(data["hard_constraints"]), "indoor_only": True}
        if "酒店" in user_text or "过夜" in user_text:
            data["hard_constraints"] = {**dict(data["hard_constraints"]), "hotel_wanted": True}
        if any(word in user_text for word in ["礼物", "花", "蛋糕", "惊喜"]):
            data["hard_constraints"] = {**dict(data["hard_constraints"]), "gift_wanted": True}
        if "怕尴尬" in user_text or "约TA" in user_text or "约ta" in user_text:
            data["relationship_stage"] = "暧昧/追求中"
            data["relationship_goal"] = "降低尴尬"
        if "纪念日" in user_text:
            data["relationship_stage"] = "纪念日"
            data["relationship_goal"] = "制造仪式感"
        return json.dumps(data, ensure_ascii=False)

