from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import replace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from activity_agent.config import ToolSettings
from activity_agent.domain.models import MerchantSupply, Scene, TimelineType
from activity_agent.providers.local_data import ProviderSnapshot, SeedLocalDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository


AMAP_BASE_URL = "https://restapi.amap.com/v3"
DEFAULT_CITY = "hangzhou"
DEFAULT_AMAP_CITY = "330100"
DEFAULT_AMAP_KEYWORDS = ("美食", "景点", "博物馆", "手作", "茶馆", "酒吧", "桌游", "密室")

CLUSTER_CENTERS: dict[str, tuple[float, float]] = {
    "hefang_old_town": (120.1694, 30.2445),
    "canal_qiaoxi": (120.1428, 30.3219),
    "westlake_hubin": (120.1608, 30.2557),
    "longwu_tea_hills": (120.0636, 30.1812),
    "xixi_wetland": (120.0639, 30.2718),
    "liangzhu_culture": (120.0114, 30.3776),
    "xianghu_lake": (120.2346, 30.1660),
    "wulin_kerry": (120.1656, 30.2714),
}

CLUSTER_ALIASES: dict[str, tuple[str, ...]] = {
    "hefang_old_town": ("河坊", "南宋", "吴山", "鼓楼", "清河坊"),
    "canal_qiaoxi": ("桥西", "运河", "拱宸桥"),
    "westlake_hubin": ("西湖", "湖滨", "南山路", "北山街"),
    "longwu_tea_hills": ("龙坞", "茶镇", "茶山"),
    "xixi_wetland": ("西溪", "湿地"),
    "liangzhu_culture": ("良渚",),
    "xianghu_lake": ("湘湖",),
    "wulin_kerry": ("武林", "嘉里", "延安路"),
}

NAME_KEYS = ("name", "名称", "景区名称", "场馆名称", "资源名称", "poi_name")
ADDRESS_KEYS = ("address", "地址", "详细地址", "位置", "资源地址")
DISTRICT_KEYS = ("district", "区县", "区", "所属区县", "行政区")
LONGITUDE_KEYS = ("longitude", "lng", "经度", "lon", "x")
LATITUDE_KEYS = ("latitude", "lat", "纬度", "y")
TYPE_KEYS = ("type", "类型", "类别", "资源类型", "行业类别")
PRICE_KEYS = ("price", "价格", "门票价格", "人均", "参考价格")
ID_KEYS = ("id", "ID", "编号", "资源编号", "景区编号")


class ProviderAPIError(Exception):
    """Raised when an external provider responds but cannot be used."""


class HTTPJSONClient:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        query = urlencode(
            {key: value for key, value in (params or {}).items() if value is not None and value != ""},
            doseq=True,
        )
        full_url = f"{url}?{query}" if query else url
        request = Request(full_url, headers={"User-Agent": "activity-agent/1.5", **(headers or {})})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                body = response.read().decode(charset, errors="replace")
        except HTTPError as exc:
            raise ProviderAPIError(f"HTTP {exc.code}: {exc.reason}") from exc
        except (TimeoutError, URLError) as exc:
            raise ProviderAPIError(str(exc)) from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderAPIError("Provider returned non-JSON response.") from exc


class AmapWebServiceClient:
    def __init__(
        self,
        api_key: str,
        http_client: HTTPJSONClient | None = None,
        base_url: str = AMAP_BASE_URL,
    ) -> None:
        if not api_key:
            raise ValueError("AMAP_API_KEY is required for real Amap calls.")
        self.api_key = api_key
        self.http_client = http_client or HTTPJSONClient()
        self.base_url = base_url.rstrip("/")

    def search_pois(
        self,
        city: str,
        keywords: str,
        types: str = "",
        offset: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        payload = self._get(
            "/place/text",
            {
                "city": city,
                "keywords": keywords,
                "types": types,
                "offset": offset,
                "page": page,
                "extensions": "all",
                "output": "JSON",
            },
        )
        self._ensure_ok(payload)
        return payload

    def search_pois_around(
        self,
        location: str,
        radius_m: int,
        keywords: str,
        types: str = "",
        offset: int = 20,
        page: int = 1,
        city: str = "",
    ) -> dict[str, Any]:
        payload = self._get(
            "/place/around",
            {
                "location": location,
                "radius": radius_m,
                "keywords": keywords,
                "city": city,
                "types": types,
                "offset": offset,
                "page": page,
                "extensions": "all",
                "sortrule": "distance",
                "output": "JSON",
            },
        )
        self._ensure_ok(payload)
        return payload

    def resolve_location(self, city: str, keyword: str) -> dict[str, Any] | None:
        payload = self.search_pois(city=city, keywords=keyword, offset=1, page=1)
        pois = payload.get("pois") or []
        return pois[0] if pois and isinstance(pois[0], dict) else None

    def weather(self, city: str, extensions: str = "base") -> dict[str, Any]:
        payload = self._get(
            "/weather/weatherInfo",
            {
                "city": city,
                "extensions": extensions,
                "output": "JSON",
            },
        )
        self._ensure_ok(payload)
        return payload

    def walking_route(self, origin: str, destination: str) -> dict[str, Any]:
        payload = self._get(
            "/direction/walking",
            {
                "origin": origin,
                "destination": destination,
                "output": "JSON",
            },
        )
        self._ensure_ok(payload)
        return payload

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = self.http_client.get_json(
            f"{self.base_url}{path}",
            {
                **params,
                "key": self.api_key,
            },
        )
        if not isinstance(payload, dict):
            raise ProviderAPIError("Amap returned an unexpected JSON array.")
        return payload

    def _ensure_ok(self, payload: dict[str, Any]) -> None:
        if str(payload.get("status")) == "1":
            return
        info = payload.get("info") or "unknown_error"
        infocode = payload.get("infocode") or "unknown_infocode"
        raise ProviderAPIError(f"Amap API failed: {info} ({infocode})")


class AmapWeatherProvider:
    provider = "amap_weather"

    def __init__(self, client: AmapWebServiceClient, city_adcode: str = DEFAULT_AMAP_CITY) -> None:
        self.client = client
        self.city_adcode = city_adcode or DEFAULT_AMAP_CITY

    def weather_hint(self, city: str, rainy: bool = False) -> ProviderSnapshot:
        try:
            payload = self.client.weather(_city_code(city, self.city_adcode), extensions="base")
            lives = payload.get("lives") or []
            if not lives:
                raise ProviderAPIError("Amap weather response did not contain lives.")
            live = lives[0]
            weather = str(live.get("weather") or "unknown")
            temperature = str(live.get("temperature") or "")
            humidity = str(live.get("humidity") or "")
            wind = "".join(str(live.get(key) or "") for key in ("winddirection", "windpower"))
            report_time = str(live.get("reporttime") or "")
            message = f"AMAP live weather: {weather}, {temperature}C, humidity {humidity}%, wind {wind}; report {report_time}."
            return ProviderSnapshot(self.provider, "live", "live", message)
        except ProviderAPIError as exc:
            if rainy:
                message = f"AMAP weather unavailable ({exc}); using indoor/rain-safe seed hint."
            else:
                message = f"AMAP weather unavailable ({exc}); using seed weather hint."
            return ProviderSnapshot(self.provider, "degraded", "seed", message)


class AmapMapDataProvider:
    provider = "amap_route"

    def __init__(
        self,
        client: AmapWebServiceClient,
        repository: SQLiteRepository,
        cache_ttl_seconds: int = 86400,
    ) -> None:
        self.client = client
        self.repository = repository
        self.cache_ttl_seconds = cache_ttl_seconds

    def route_summary(self, area_clusters: list[str]) -> ProviderSnapshot:
        clusters = _unique_known_clusters(area_clusters)
        if len(clusters) < 2:
            return ProviderSnapshot(
                self.provider,
                "same_area",
                "seed",
                "Single-area plan; no cross-area AMAP route leg was needed.",
            )

        query_hash = hashlib.sha1("|".join(clusters).encode("utf-8")).hexdigest()
        cached = self.repository.get_api_cache(self.provider, query_hash)
        if cached:
            return ProviderSnapshot(
                self.provider,
                "cached",
                "live",
                str(cached.get("message", "AMAP route loaded from cache.")),
            )

        try:
            legs = []
            total_distance_m = 0
            total_duration_s = 0
            for origin_cluster, destination_cluster in zip(clusters, clusters[1:]):
                origin = _cluster_location(origin_cluster)
                destination = _cluster_location(destination_cluster)
                payload = self.client.walking_route(origin, destination)
                path = _first_route_path(payload)
                distance_m = _safe_int(path.get("distance"), 0)
                duration_s = _safe_int(path.get("duration"), 0)
                total_distance_m += distance_m
                total_duration_s += duration_s
                legs.append(
                    {
                        "origin_cluster": origin_cluster,
                        "destination_cluster": destination_cluster,
                        "distance_m": distance_m,
                        "duration_s": duration_s,
                    }
                )
            minutes = max(1, round(total_duration_s / 60))
            distance_km = total_distance_m / 1000
            message = f"AMAP walking route: {distance_km:.1f} km, about {minutes} min across {len(legs)} leg(s)."
            self.repository.save_api_cache(
                self.provider,
                query_hash,
                "ok",
                self.cache_ttl_seconds,
                {"message": message, "area_clusters": clusters, "legs": legs},
            )
            return ProviderSnapshot(self.provider, "live", "live", message)
        except ProviderAPIError as exc:
            return ProviderSnapshot(
                self.provider,
                "degraded",
                "seed",
                f"AMAP route unavailable ({exc}); using seed route estimate.",
            )


class HangzhouOpenDataClient:
    def __init__(
        self,
        api_url: str,
        http_client: HTTPJSONClient | None = None,
        app_key: str | None = None,
        app_secret: str | None = None,
        token: str | None = None,
        default_params: dict[str, Any] | None = None,
    ) -> None:
        if not api_url:
            raise ValueError("HANGZHOU_OPEN_DATA_API_URL is required.")
        self.api_url = api_url
        self.http_client = http_client or HTTPJSONClient()
        self.app_key = app_key
        self.app_secret = app_secret
        self.token = token
        self.default_params = default_params or {}

    def fetch_records(
        self,
        city: str = DEFAULT_CITY,
        keywords: list[str] | None = None,
        area: str | None = None,
    ) -> list[dict[str, Any]]:
        params = dict(self.default_params)
        params.setdefault("city", city)
        if keywords:
            params.setdefault("keyword", ",".join(keywords))
        if area:
            params.setdefault("area", area)
        if self.app_key:
            params.setdefault("appKey", self.app_key)
        if self.app_secret:
            params.setdefault("appSecret", self.app_secret)

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = self.http_client.get_json(self.api_url, params=params, headers=headers)
        return _extract_records(payload)


class HybridLiveDataProvider(SeedLocalDataProvider):
    """Seed catalog plus opt-in real provider syncs."""

    def __init__(
        self,
        repository: SQLiteRepository,
        settings: ToolSettings,
        amap_client: AmapWebServiceClient | None = None,
        hangzhou_client: HangzhouOpenDataClient | None = None,
    ) -> None:
        super().__init__(repository)
        self.settings = settings
        timeout = HTTPJSONClient(settings.http_timeout_seconds)
        self.amap_client = amap_client or (
            AmapWebServiceClient(settings.amap_api_key, timeout) if settings.amap_api_key else None
        )
        self.hangzhou_client = hangzhou_client or _build_hangzhou_open_data_client(settings, timeout)

    def sync_live_sources(
        self,
        city: str = DEFAULT_CITY,
        keywords: list[str] | None = None,
        area: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        requested_keywords = [item.strip() for item in (keywords or _configured_keywords(self.settings)) if item.strip()]
        sources: dict[str, Any] = {}
        errors: dict[str, str] = {}
        all_supplies: list[MerchantSupply] = []

        amap_supplies = self._sync_amap_pois(city, requested_keywords, area, errors)
        if amap_supplies:
            self.repository.upsert_supplies(amap_supplies, "amap_poi")
            all_supplies.extend(amap_supplies)
        sources["amap_poi"] = {"places": len(amap_supplies), "configured": self.amap_client is not None}

        hangzhou_supplies = self._sync_hangzhou_open_data(city, requested_keywords, area, errors)
        if hangzhou_supplies:
            self.repository.upsert_supplies(hangzhou_supplies, "hangzhou_open_data")
            all_supplies.extend(hangzhou_supplies)
        sources["hangzhou_open_data"] = {
            "places": len(hangzhou_supplies),
            "configured": self.hangzhou_client is not None,
        }

        status = "live_synced" if all_supplies else "seed_synced"
        if errors and all_supplies:
            status = "partially_synced"
        elif errors and not all_supplies:
            status = "degraded_to_seed"

        return {
            "city": city,
            "status": status,
            "data_mode": self.settings.data_mode,
            "places": len(self.list_supplies(city)),
            "live_places": len(all_supplies),
            "sources": sources,
            "errors": errors,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "message": _sync_message(status, sources, errors),
        }

    def sync_theme_pois(
        self,
        city: str,
        keywords: list[str],
        origin_longitude: float | None,
        origin_latitude: float | None,
        radius_km: float = 5.0,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        errors: dict[str, str] = {}
        sources: dict[str, Any] = {}
        supplies_by_id: dict[str, MerchantSupply] = {}

        if self.amap_client:
            location = _format_location(origin_longitude, origin_latitude)
            radius_m = int(max(1.0, radius_km) * 1000)
            for keyword in keywords:
                try:
                    if location:
                        payload = self.amap_client.search_pois_around(
                            location=location,
                            radius_m=radius_m,
                            keywords=keyword,
                            city=_city_code(city, self.settings.amap_city),
                            types=self.settings.amap_poi_types,
                            offset=20,
                            page=1,
                        )
                    else:
                        payload = self.amap_client.search_pois(
                            city=_city_code(city, self.settings.amap_city),
                            keywords=keyword,
                            types=self.settings.amap_poi_types,
                            offset=20,
                            page=1,
                        )
                except ProviderAPIError as exc:
                    errors[f"amap_poi:{keyword}"] = str(exc)
                    continue

                for poi in payload.get("pois") or []:
                    if not isinstance(poi, dict):
                        continue
                    supply = _amap_poi_to_supply(poi, keyword, city)
                    current = supplies_by_id.get(supply.id)
                    supplies_by_id[supply.id] = _merge_supply_keyword(current, supply, keyword) if current else supply
        else:
            errors["amap_poi"] = "AMAP_API_KEY is not configured."

        amap_supplies = list(supplies_by_id.values())[:30]
        if amap_supplies:
            self.repository.upsert_supplies(amap_supplies, "amap_theme_poi")
        sources["amap_poi"] = {"places": len(amap_supplies), "configured": self.amap_client is not None}

        hangzhou_supplies = self._sync_hangzhou_open_data(city, keywords, area=None, errors=errors)[:30]
        if hangzhou_supplies:
            self.repository.upsert_supplies(hangzhou_supplies, "hangzhou_open_data")
        sources["hangzhou_open_data"] = {
            "places": len(hangzhou_supplies),
            "configured": self.hangzhou_client is not None,
        }

        live_places = len(amap_supplies) + len(hangzhou_supplies)
        status = "live_synced" if live_places else ("degraded_to_seed" if errors else "empty")
        if live_places and errors:
            status = "partially_synced"
        return {
            "status": status,
            "live_places": live_places,
            "sources": sources,
            "errors": errors,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }

    def _sync_amap_pois(
        self,
        city: str,
        keywords: list[str],
        area: str | None,
        errors: dict[str, str],
    ) -> list[MerchantSupply]:
        if not self.amap_client:
            errors["amap_poi"] = "AMAP_API_KEY is not configured."
            return []

        supplies_by_id: dict[str, MerchantSupply] = {}
        for keyword in keywords or list(DEFAULT_AMAP_KEYWORDS):
            try:
                payload = self.amap_client.search_pois(
                    city=_city_code(city, self.settings.amap_city),
                    keywords=keyword,
                    types=self.settings.amap_poi_types,
                    offset=20,
                    page=1,
                )
            except ProviderAPIError as exc:
                errors[f"amap_poi:{keyword}"] = str(exc)
                continue
            for poi in payload.get("pois") or []:
                if not isinstance(poi, dict):
                    continue
                supply = _amap_poi_to_supply(poi, keyword, city)
                if area and supply.area_cluster != area:
                    continue
                current = supplies_by_id.get(supply.id)
                supplies_by_id[supply.id] = _merge_supply_keyword(current, supply, keyword) if current else supply
        return list(supplies_by_id.values())

    def _sync_hangzhou_open_data(
        self,
        city: str,
        keywords: list[str],
        area: str | None,
        errors: dict[str, str],
    ) -> list[MerchantSupply]:
        if not self.hangzhou_client:
            return []

        try:
            records = self.hangzhou_client.fetch_records(city=city, keywords=keywords, area=area)
        except ProviderAPIError as exc:
            errors["hangzhou_open_data"] = str(exc)
            return []

        supplies = []
        for record in records:
            supply = _open_data_record_to_supply(record, city)
            if supply:
                supplies.append(supply)
        return supplies


def _build_hangzhou_open_data_client(
    settings: ToolSettings,
    http_client: HTTPJSONClient,
) -> HangzhouOpenDataClient | None:
    if not settings.hangzhou_open_data_api_url:
        return None
    return HangzhouOpenDataClient(
        settings.hangzhou_open_data_api_url,
        http_client=http_client,
        app_key=settings.hangzhou_open_data_app_key,
        app_secret=settings.hangzhou_open_data_app_secret,
        token=settings.hangzhou_open_data_token,
        default_params=_json_params(settings.hangzhou_open_data_params),
    )


def _json_params(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _configured_keywords(settings: ToolSettings) -> list[str]:
    keywords = [item.strip() for item in settings.amap_poi_keywords.split(",")]
    return [item for item in keywords if item] or list(DEFAULT_AMAP_KEYWORDS)


def _city_code(city: str, fallback: str = DEFAULT_AMAP_CITY) -> str:
    normalized = str(city or "").strip().lower()
    if normalized in {"hangzhou", "hz", "杭州", "杭州市"}:
        return fallback or DEFAULT_AMAP_CITY
    return str(city or fallback)


def _unique_known_clusters(area_clusters: list[str]) -> list[str]:
    clusters: list[str] = []
    for cluster in area_clusters:
        if cluster in CLUSTER_CENTERS and cluster not in clusters:
            clusters.append(cluster)
    return clusters


def _cluster_location(cluster: str) -> str:
    lng, lat = CLUSTER_CENTERS[cluster]
    return f"{lng},{lat}"


def _first_route_path(payload: dict[str, Any]) -> dict[str, Any]:
    route = payload.get("route") or {}
    paths = route.get("paths") or []
    if not paths:
        raise ProviderAPIError("Amap route response did not contain paths.")
    path = paths[0]
    if not isinstance(path, dict):
        raise ProviderAPIError("Amap route path was not an object.")
    return path


def _extract_records(payload: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    candidates: list[Any] = [payload]
    for key in ("data", "result", "rows", "records", "list", "datas", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            candidates.append(value)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in ("data", "result", "rows", "records", "list", "datas", "items"):
            value = candidate.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _amap_poi_to_supply(poi: dict[str, Any], keyword: str, city: str) -> MerchantSupply:
    poi_id = str(poi.get("id") or _stable_id(poi))
    name = str(poi.get("name") or keyword)
    type_text = " ".join(str(poi.get(key) or "") for key in ("type", "typecode", "biz_type"))
    location = _parse_location(str(poi.get("location") or ""))
    area_cluster = _infer_area_cluster(name, str(poi.get("address") or ""), location)
    timeline_type = _classify_supply_type(name, type_text)
    price = _price_from_amap(poi, timeline_type)
    lng, lat = location if location else (None, None)
    tags = _tags_from_text(keyword, type_text, name)
    return MerchantSupply(
        id=f"amap_{_safe_identifier(poi_id)}",
        name=name,
        type=timeline_type,
        price=price,
        duration_minutes=_default_duration(timeline_type),
        distance_km=_distance_to_cluster_km(location, area_cluster) if location else 1.5,
        district=str(poi.get("adname") or poi.get("business_area") or ""),
        tags=tags,
        scene_fit=[Scene.FRIENDS, Scene.COUPLE],
        booking_modes=_booking_modes_for(timeline_type),
        available=True,
        why="Matched from Amap POI search; verify live booking, price, and hours before confirmation.",
        source="amap_poi",
        source_id=poi_id,
        city=_normalize_city(city),
        address=str(poi.get("address") or ""),
        latitude=lat,
        longitude=lng,
        area_cluster=area_cluster,
        open_dayparts=["morning", "afternoon", "evening"],
        weather_fit=_weather_fit_for(timeline_type, type_text),
        checkin_value="Amap POI",
        local_flavor_tags=tags[:4],
        transport_hint="Route refresh can use AMAP directions when this POI is part of a selected plan.",
        data_confidence="live",
        matched_keywords=[keyword],
    )


def _open_data_record_to_supply(record: dict[str, Any], city: str) -> MerchantSupply | None:
    name = _first_text(record, NAME_KEYS)
    if not name:
        return None
    address = _first_text(record, ADDRESS_KEYS)
    district = _first_text(record, DISTRICT_KEYS)
    type_text = _first_text(record, TYPE_KEYS)
    lng = _first_float(record, LONGITUDE_KEYS)
    lat = _first_float(record, LATITUDE_KEYS)
    location = (lng, lat) if lng is not None and lat is not None else None
    timeline_type = _classify_supply_type(name, type_text)
    area_cluster = _infer_area_cluster(name, address, location)
    source_id = _first_text(record, ID_KEYS) or _stable_id(record)
    tags = _tags_from_text(type_text or "official", address, name)
    return MerchantSupply(
        id=f"hzopen_{_safe_identifier(source_id)}",
        name=name,
        type=timeline_type,
        price=_first_price(record, PRICE_KEYS) or _default_price(timeline_type),
        duration_minutes=_default_duration(timeline_type),
        distance_km=_distance_to_cluster_km(location, area_cluster) if location else 1.5,
        district=district,
        tags=tags,
        scene_fit=[Scene.FRIENDS, Scene.COUPLE],
        booking_modes=_booking_modes_for(timeline_type),
        available=True,
        why="Matched from Hangzhou Open Data; verify current operation details before confirmation.",
        source="hangzhou_open_data",
        source_id=source_id,
        city=_normalize_city(city),
        address=address,
        latitude=lat,
        longitude=lng,
        area_cluster=area_cluster,
        open_dayparts=["morning", "afternoon", "evening"],
        weather_fit=_weather_fit_for(timeline_type, type_text),
        checkin_value="official_open_data",
        local_flavor_tags=tags[:4],
        transport_hint="Official Hangzhou Open Data record; route refresh can use AMAP directions.",
        data_confidence="official",
    )


def _parse_location(value: str) -> tuple[float, float] | None:
    if not value or "," not in value:
        return None
    try:
        lng_text, lat_text = value.split(",", 1)
        return float(lng_text), float(lat_text)
    except ValueError:
        return None


def _format_location(longitude: float | None, latitude: float | None) -> str:
    if longitude is None or latitude is None:
        return ""
    return f"{longitude},{latitude}"


def _merge_supply_keyword(current: MerchantSupply | None, incoming: MerchantSupply, keyword: str) -> MerchantSupply:
    if current is None:
        return incoming
    keywords = list(dict.fromkeys([*current.matched_keywords, *incoming.matched_keywords, keyword]))
    tags = list(dict.fromkeys([*current.tags, *incoming.tags]))
    local_tags = list(dict.fromkeys([*current.local_flavor_tags, *incoming.local_flavor_tags]))
    return replace(current, matched_keywords=keywords, tags=tags[:8], local_flavor_tags=local_tags[:8])


def _infer_area_cluster(name: str, address: str, location: tuple[float, float] | None) -> str:
    text = f"{name} {address}"
    for cluster, aliases in CLUSTER_ALIASES.items():
        if any(alias in text for alias in aliases):
            return cluster
    if location:
        return min(CLUSTER_CENTERS, key=lambda cluster: _distance_to_cluster_km(location, cluster))
    return "wulin_kerry"


def _distance_to_cluster_km(location: tuple[float, float] | None, cluster: str) -> float:
    if not location or cluster not in CLUSTER_CENTERS:
        return 1.5
    return round(_haversine_km(location[1], location[0], CLUSTER_CENTERS[cluster][1], CLUSTER_CENTERS[cluster][0]), 2)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _classify_supply_type(name: str, type_text: str) -> TimelineType:
    text = f"{name} {type_text}"
    if "酒店" in text or "宾馆" in text or "旅馆" in text or "10" == str(type_text)[:2]:
        return TimelineType.HOTEL
    if any(token in text for token in ("餐饮", "美食", "火锅", "饭店", "餐厅", "咖啡", "茶餐厅")) or str(type_text).startswith("05"):
        return TimelineType.DINING
    if any(token in text for token in ("酒吧", "KTV", "夜店", "夜总会")):
        return TimelineType.NIGHTLIFE
    if any(token in text for token in ("茶馆", "足疗", "按摩", "SPA", "休闲")):
        return TimelineType.RELAX
    if any(token in text for token in ("景点", "风景", "名胜", "公园", "西湖", "湿地", "博物馆")) or str(type_text).startswith("11"):
        return TimelineType.CHECKIN
    if any(token in text for token in ("花店", "礼品", "蛋糕")):
        return TimelineType.GIFT
    return TimelineType.ACTIVITY


def _price_from_amap(poi: dict[str, Any], timeline_type: TimelineType) -> int:
    biz_ext = poi.get("biz_ext") if isinstance(poi.get("biz_ext"), dict) else {}
    cost = biz_ext.get("cost") if biz_ext else None
    return _parse_price(cost) or _default_price(timeline_type)


def _first_price(record: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        price = _parse_price(record.get(key))
        if price is not None:
            return price
    return None


def _parse_price(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    if not match:
        return None
    return max(0, int(round(float(match.group(0)))))


def _default_price(timeline_type: TimelineType) -> int:
    return {
        TimelineType.ACTIVITY: 90,
        TimelineType.DINING: 120,
        TimelineType.CHECKIN: 40,
        TimelineType.RELAX: 90,
        TimelineType.NIGHTLIFE: 120,
        TimelineType.HOTEL: 600,
        TimelineType.GIFT: 150,
    }.get(timeline_type, 80)


def _default_duration(timeline_type: TimelineType) -> int:
    return {
        TimelineType.DINING: 90,
        TimelineType.CHECKIN: 60,
        TimelineType.HOTEL: 720,
        TimelineType.GIFT: 20,
        TimelineType.RELAX: 75,
        TimelineType.NIGHTLIFE: 90,
    }.get(timeline_type, 75)


def _booking_modes_for(timeline_type: TimelineType) -> list[str]:
    if timeline_type == TimelineType.HOTEL:
        return ["hotel"]
    if timeline_type == TimelineType.GIFT:
        return ["instant_delivery"]
    if timeline_type in {TimelineType.CHECKIN, TimelineType.ACTIVITY}:
        return ["ticket", "reservation"]
    if timeline_type in {TimelineType.DINING, TimelineType.RELAX, TimelineType.NIGHTLIFE}:
        return ["reservation"]
    return ["offline_check"]


def _weather_fit_for(timeline_type: TimelineType, type_text: str) -> list[str]:
    if timeline_type == TimelineType.CHECKIN and "室内" not in type_text and "博物馆" not in type_text:
        return ["sunny", "cloudy", "light_rain"]
    return ["sunny", "cloudy", "rainy", "light_rain"]


def _tags_from_text(*values: str) -> list[str]:
    tags: list[str] = []
    for value in values:
        for piece in re.split(r"[,，;；\s/|]+", str(value or "")):
            piece = piece.strip()
            if piece and piece not in tags:
                tags.append(piece)
    return tags[:8] or ["live"]


def _first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if value not in {None, ""}:
            return str(value)
    return ""


def _first_float(record: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = record.get(key)
        if value in {None, ""}:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _stable_id(value: Any) -> str:
    return hashlib.sha1(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _safe_identifier(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value))
    return cleaned.strip("_")[:40] or _stable_id(value)


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _normalize_city(city: str) -> str:
    normalized = str(city or "").strip().lower()
    return DEFAULT_CITY if normalized in {"", "hangzhou", "hz", "杭州", "杭州市", "330100"} else normalized


def _sync_message(status: str, sources: dict[str, Any], errors: dict[str, str]) -> str:
    if status == "live_synced":
        return "Live provider data synced from configured real APIs."
    if status == "partially_synced":
        return "Some real APIs synced successfully; failed sources were left on seed fallback."
    if errors:
        return "No real provider data was synced; using seed fallback. Check provider API keys and URLs."
    return "Seed catalog is current; no real provider source was configured."
