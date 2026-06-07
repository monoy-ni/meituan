from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from activity_agent.data import SUPPLY_CATALOG
from activity_agent.data.hangzhou_catalog import HANGZHOU_ROUTE_CLUSTERS, HANGZHOU_THEME_TEMPLATES
from activity_agent.domain.models import MerchantSupply, TimelineType, ToolEvent
from activity_agent.storage.sqlite_repository import SQLiteRepository
from activity_agent.tools.mock_meituan import MockMeituanToolClient, ToolResult


class LocalDataProvider(Protocol):
    def list_supplies(self, city: str = "hangzhou") -> list[MerchantSupply]:
        ...

    def list_route_clusters(self, city: str = "hangzhou") -> list[dict[str, object]]:
        ...

    def list_theme_templates(self, city: str = "hangzhou") -> list[dict[str, object]]:
        ...

    def search_supplies(self, filters: dict[str, object]) -> list[MerchantSupply]:
        ...


class MapDataProvider(Protocol):
    def route_summary(self, area_clusters: list[str]) -> "ProviderSnapshot":
        ...


class WeatherProvider(Protocol):
    def weather_hint(self, city: str, rainy: bool = False) -> "ProviderSnapshot":
        ...


class CommerceProvider(Protocol):
    def merchant_profile(self, merchant_id: str, merchant_name: str | None = None) -> ToolResult:
        ...

    def check_availability(self, merchant_id: str, time_window: str, party_size: int) -> ToolResult:
        ...

    def create_booking_hold(self, items: list[dict[str, object]]) -> ToolResult:
        ...

    def create_aa_draft(self, total: int, party_size: int, mode: str) -> ToolResult:
        ...

    def confirm_booking(self, hold_id: str, confirm_token: str, items: list[dict[str, object]]) -> ToolResult:
        ...


@dataclass(frozen=True)
class ProviderSnapshot:
    provider: str
    status: str
    data_confidence: str
    message: str


class SeedLocalDataProvider:
    """SQLite-backed seed provider for Hangzhou demo supply."""

    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository
        self.repository.seed_local_catalog(SUPPLY_CATALOG, HANGZHOU_ROUTE_CLUSTERS, HANGZHOU_THEME_TEMPLATES)

    def list_supplies(self, city: str = "hangzhou") -> list[MerchantSupply]:
        return self.repository.list_local_supplies(city)

    def list_route_clusters(self, city: str = "hangzhou") -> list[dict[str, object]]:
        return self.repository.list_route_clusters(city)

    def list_theme_templates(self, city: str = "hangzhou") -> list[dict[str, object]]:
        return self.repository.list_theme_templates(city)

    def search_supplies(self, filters: dict[str, object]) -> list[MerchantSupply]:
        supplies = self.list_supplies(str(filters.get("city") or "hangzhou"))
        item_type = filters.get("type")
        tags = set(filters.get("tags") or [])
        max_price = int(filters.get("max_price") or 10_000)
        max_distance = float(filters.get("max_distance") or 99)
        area_cluster = str(filters.get("area_cluster") or "")

        matches = [
            supply
            for supply in supplies
            if supply.available
            and (item_type is None or supply.type == TimelineType(str(item_type)))
            and supply.price <= max_price
            and supply.distance_km <= max_distance
            and (not area_cluster or supply.area_cluster == area_cluster)
        ]
        matches.sort(
            key=lambda supply: (
                -len(tags & set([*supply.tags, *supply.local_flavor_tags])),
                supply.price,
                supply.distance_km,
            )
        )
        return matches


class MockMapDataProvider:
    """Provider-shaped map adapter. First release stays offline and cache-friendly."""

    provider = "seed_map"

    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository

    def route_summary(self, area_clusters: list[str]) -> ProviderSnapshot:
        query_hash = hashlib.sha1("|".join(area_clusters).encode("utf-8")).hexdigest()
        cached = self.repository.get_api_cache(self.provider, query_hash)
        if cached:
            return ProviderSnapshot(
                provider=self.provider,
                status="cached",
                data_confidence="cache",
                message=str(cached.get("message", "路线耗时来自缓存估算。")),
            )

        message = "同片区步行为主，路线耗时为 seed 估算。"
        if len(set(area_clusters)) > 1:
            message = "包含跨片区移动，建议出发前刷新地图路线。"
        self.repository.save_api_cache(
            self.provider,
            query_hash,
            "ok",
            86400,
            {"message": message, "area_clusters": area_clusters},
        )
        return ProviderSnapshot(provider=self.provider, status="seed", data_confidence="seed", message=message)


class MockWeatherProvider:
    provider = "seed_weather"

    def weather_hint(self, city: str, rainy: bool = False) -> ProviderSnapshot:
        if rainy:
            return ProviderSnapshot(self.provider, "seed", "seed", "按雨天偏好优先室内和低天气风险供给。")
        return ProviderSnapshot(self.provider, "seed", "seed", "天气未实时刷新，室外点需出发前确认。")


class MockCommerceProvider:
    """Commerce adapter that preserves the current safe mock booking behavior."""

    def __init__(self, tool_client: MockMeituanToolClient) -> None:
        self.tool_client = tool_client

    def check_availability(self, merchant_id: str, time_window: str, party_size: int) -> ToolResult:
        return self.tool_client.check_availability(merchant_id, time_window, party_size)

    def merchant_profile(self, merchant_id: str, merchant_name: str | None = None) -> ToolResult:
        return self.tool_client.merchant_profile(merchant_id, merchant_name)

    def create_booking_hold(self, items: list[dict[str, object]]) -> ToolResult:
        return self.tool_client.create_booking_hold(items)

    def create_aa_draft(self, total: int, party_size: int, mode: str) -> ToolResult:
        return self.tool_client.create_aa_draft(total, party_size, mode)

    def confirm_booking(self, hold_id: str, confirm_token: str, items: list[dict[str, object]]) -> ToolResult:
        return self.tool_client.confirm_booking(hold_id, confirm_token, items)
