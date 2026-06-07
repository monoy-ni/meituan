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
    amap_city: str = "330100"
    amap_poi_keywords: str = "美食,景点,博物馆,手作,茶馆,酒吧,桌游,密室"
    amap_poi_types: str = ""
    tencent_map_api_key: str | None = None
    hangzhou_open_data_api_url: str | None = None
    hangzhou_open_data_app_key: str | None = None
    hangzhou_open_data_app_secret: str | None = None
    hangzhou_open_data_token: str | None = None
    hangzhou_open_data_params: str | None = None
    http_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "ToolSettings":
        return cls(
            mode=os.getenv("ACTIVITY_AGENT_TOOL_MODE", cls.mode),
            data_mode=os.getenv("ACTIVITY_AGENT_DATA_MODE", cls.data_mode),
            map_provider=os.getenv("ACTIVITY_AGENT_MAP_PROVIDER", cls.map_provider),
            amap_api_key=os.getenv("AMAP_API_KEY") or None,
            amap_city=os.getenv("AMAP_CITY", cls.amap_city),
            amap_poi_keywords=os.getenv("AMAP_POI_KEYWORDS", cls.amap_poi_keywords),
            amap_poi_types=os.getenv("AMAP_POI_TYPES", cls.amap_poi_types),
            tencent_map_api_key=os.getenv("TENCENT_MAP_API_KEY") or None,
            hangzhou_open_data_api_url=os.getenv("HANGZHOU_OPEN_DATA_API_URL") or None,
            hangzhou_open_data_app_key=(
                os.getenv("HANGZHOU_OPEN_DATA_APP_KEY")
                or os.getenv("HANGZHOU_OPEN_DATA_APP_ID")
                or None
            ),
            hangzhou_open_data_app_secret=os.getenv("HANGZHOU_OPEN_DATA_APP_SECRET") or None,
            hangzhou_open_data_token=os.getenv("HANGZHOU_OPEN_DATA_TOKEN") or None,
            hangzhou_open_data_params=os.getenv("HANGZHOU_OPEN_DATA_PARAMS") or None,
            http_timeout_seconds=float(os.getenv("ACTIVITY_AGENT_HTTP_TIMEOUT_SECONDS", str(cls.http_timeout_seconds))),
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
