from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    timeout_seconds: float = 20.0

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            base_url=os.getenv("ACTIVITY_AGENT_LLM_BASE_URL", cls.base_url),
            api_key=os.getenv("ACTIVITY_AGENT_LLM_API_KEY") or None,
            model=os.getenv("ACTIVITY_AGENT_LLM_MODEL", cls.model),
            temperature=float(os.getenv("ACTIVITY_AGENT_LLM_TEMPERATURE", str(cls.temperature))),
            timeout_seconds=float(os.getenv("ACTIVITY_AGENT_LLM_TIMEOUT_SECONDS", str(cls.timeout_seconds))),
        )


@dataclass(frozen=True)
class StorageSettings:
    path: str = "./activity_agent.sqlite3"

    @classmethod
    def from_env(cls) -> "StorageSettings":
        return cls(path=os.getenv("ACTIVITY_AGENT_STORAGE_PATH", cls.path))


@dataclass(frozen=True)
class ToolSettings:
    mode: str = "mock"
    data_mode: str = "seed"
    map_provider: str = "none"
    amap_api_key: str | None = None
    tencent_map_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "ToolSettings":
        return cls(
            mode=os.getenv("ACTIVITY_AGENT_TOOL_MODE", cls.mode),
            data_mode=os.getenv("ACTIVITY_AGENT_DATA_MODE", cls.data_mode),
            map_provider=os.getenv("ACTIVITY_AGENT_MAP_PROVIDER", cls.map_provider),
            amap_api_key=os.getenv("AMAP_API_KEY") or None,
            tencent_map_api_key=os.getenv("TENCENT_MAP_API_KEY") or None,
        )


@dataclass(frozen=True)
class AgentSettings:
    llm: LLMSettings
    storage: StorageSettings
    tools: ToolSettings

    @classmethod
    def from_env(cls) -> "AgentSettings":
        return cls(
            llm=LLMSettings.from_env(),
            storage=StorageSettings.from_env(),
            tools=ToolSettings.from_env(),
        )
