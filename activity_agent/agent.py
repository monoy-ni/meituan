from __future__ import annotations

import math
import re
from dataclasses import replace
from typing import Any

from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.data.theme_keyword_seeds import keyword_seeds_for_theme
from activity_agent.domain.models import (
    AgentResponse,
    AfterActionReview,
    BookingConfirmation,
    BookingDraft,
    FeedbackStatus,
    Intent,
    InviteFeedback,
    PayMode,
    PlanningResult,
    PlanOption,
    RouteResult,
    Scene,
    Session,
    UserRequest,
)
from activity_agent.llm import LLMClient, LLMItineraryCurator, LLMKeywordExpander, MockLLMClient, OpenAICompatibleLLMClient
from activity_agent.modules.booking_orchestrator import BookingOrchestrator
from activity_agent.modules.context_collector import ContextCollector
from activity_agent.modules.dialogue_manager import DialogueManager, DialogueState
from activity_agent.modules.feedback_resolver import FeedbackResolver
from activity_agent.modules.intent_router import IntentRouter
from activity_agent.modules.itinerary_composer import ItineraryComposer
from activity_agent.modules.review_memory import ReviewMemory
from activity_agent.modules.share_card_generator import ShareCardGenerator
from activity_agent.modules.theme_planner import ThemePlanner
from activity_agent.providers import (
    AmapMapDataProvider,
    AmapWeatherProvider,
    AmapWebServiceClient,
    HybridLiveDataProvider,
    MockCommerceProvider,
    MockMapDataProvider,
    MockWeatherProvider,
    SeedLocalDataProvider,
)
from activity_agent.storage import SQLiteRepository
from activity_agent.tools import MockMeituanToolClient


class ActivityPlanningAgent:
    """Python SDK facade for the local activity planning Agent MVP."""

    def __init__(
        self,
        settings: AgentSettings | None = None,
        llm_client: LLMClient | None = None,
        repository: SQLiteRepository | None = None,
        tool_client: MockMeituanToolClient | None = None,
    ) -> None:
        self.settings = settings or AgentSettings(
            llm=LLMSettings(),
            storage=StorageSettings(path=":memory:"),
            tools=ToolSettings(),
        )
        self.repository = repository or SQLiteRepository(self.settings.storage.path)
        self.local_data_provider = self._build_local_data_provider()
        local_catalog = self.local_data_provider.list_supplies("hangzhou")
        self.tool_client = tool_client or MockMeituanToolClient(local_catalog)
        self.map_provider = self._build_map_provider()
        self.weather_provider = self._build_weather_provider()
        self.commerce_provider = MockCommerceProvider(self.tool_client)
        
        # 简化 LLM 客户端选择 - 直接选择，没有降级逻辑
        self.llm_client = llm_client or (
            OpenAICompatibleLLMClient(self.settings.llm) if self.settings.llm.api_key else MockLLMClient()
        )
        self.keyword_expander = LLMKeywordExpander(self.llm_client)
        self.itinerary_curator = LLMItineraryCurator(self.llm_client)

        self.intent_router = IntentRouter()
        self.context_collector = ContextCollector()
        self.theme_planner = ThemePlanner()
        from activity_agent.modules.supply_matcher import SupplyMatcher

        self.supply_matcher = SupplyMatcher(local_catalog)
        self.itinerary_composer = ItineraryComposer(self.supply_matcher)
        self.share_card_generator = ShareCardGenerator()
        self.feedback_resolver = FeedbackResolver(self.theme_planner, self.itinerary_composer)
        self.booking_orchestrator = BookingOrchestrator(self.commerce_provider)
        self.review_memory = ReviewMemory()
        self.dialogue_manager = DialogueManager(self.llm_client)

    @classmethod
    def from_env(cls) -> "ActivityPlanningAgent":
        settings = AgentSettings.from_env()
        return cls(settings=settings)

    def _build_local_data_provider(self):
        if str(self.settings.tools.data_mode).lower() in {"hybrid", "live", "real"}:
            return HybridLiveDataProvider(self.repository, self.settings.tools)
        return SeedLocalDataProvider(self.repository)

    def _build_map_provider(self):
        if self._use_amap() and self.settings.tools.amap_api_key:
            client = AmapWebServiceClient(self.settings.tools.amap_api_key)
            return AmapMapDataProvider(client, self.repository)
        return MockMapDataProvider(self.repository)

    def _build_weather_provider(self):
        if self._use_amap() and self.settings.tools.amap_api_key:
            client = AmapWebServiceClient(self.settings.tools.amap_api_key)
            return AmapWeatherProvider(client, self.settings.tools.amap_city)
        return MockWeatherProvider()

    def _use_amap(self) -> bool:
        return str(self.settings.tools.map_provider).lower() == "amap"

    def _refresh_runtime_catalog(self, city: str = "hangzhou") -> None:
        local_catalog = self.local_data_provider.list_supplies(city)
        self.tool_client.catalog = local_catalog
        from activity_agent.modules.supply_matcher import SupplyMatcher

        self.supply_matcher = SupplyMatcher(local_catalog)
        self.itinerary_composer = ItineraryComposer(self.supply_matcher)

    def start_session(self, user_id: str | None = None) -> Session:
        return self.repository.create_session(user_id)

    def close(self) -> None:
        self.repository.close()

    def list_hangzhou_themes(self) -> list[dict[str, object]]:
        return self.local_data_provider.list_theme_templates("hangzhou")

    def featured_itineraries(
        self,
        city: str = "hangzhou",
        duration: str | None = None,
        date: str | None = None,
    ) -> PlanningResult:
        duration_text = "一日" if duration == "full_day" else "半日"
        text = f"{city} {duration_text} 不想查攻略 直接安排 老城烟火 西湖 运河 特色美食"
        if date:
            text += f" {date}"
        return self.plan(text, scene_hint=Scene.FRIENDS)

    def generate_itineraries(
        self,
        session_id: str,
        city: str = "hangzhou",
        theme_id: str | None = None,
        message: str | None = None,
        budget_per_person: int | None = None,
        duration: str | None = None,
        party_size: int | None = None,
        location: str | None = None,
        time_window: str | None = None,
        experience_tags: list[str] | None = None,
        effort_preference: str | None = None,
        weather: str | None = None,
        search_radius_km: float | None = None,
        route_limit_km: float | None = None,
        route_limit_minutes: int | None = None,
    ) -> AgentResponse:
        self._ensure_session(session_id)
        theme = self._theme_prompt(theme_id)
        city_name = "杭州" if city in {"hangzhou", "杭州"} else city
        text = message or f"{city_name} 不想查攻略 直接安排 {theme}"
        if budget_per_person:
            text += f"，人均预算{budget_per_person}"
        if duration == "full_day":
            text += "，一整天"
        elif duration == "half_day":
            text += "，半天"
        if party_size:
            text += f"，{party_size}个人"
        if location:
            text += f"，从{location}附近出发"
        if time_window:
            text += f"，时间{time_window}"
        if experience_tags:
            text += "，想要" + "、".join(experience_tags)
        if effort_preference in {"low", "低", "少走路"}:
            text += "，不想太累，少走路"
        if weather in {"rain", "rainy", "下雨", "雨天"}:
            text += "，下雨，优先室内"
        if search_radius_km:
            text += f"，周边{search_radius_km}公里"
        if route_limit_km:
            text += f"，路线控制在{route_limit_km}公里"
        if route_limit_minutes:
            text += f"，{route_limit_minutes}分钟内"
        return self.chat(session_id, text)

    def refresh_itinerary(self, session_id: str, itinerary_id: str) -> dict[str, object]:
        latest = self._latest_planning_or_raise(session_id)
        request = latest["request"]
        option = self._find_option(latest["options"], itinerary_id)
        area_clusters = [item.area_cluster for item in option.timeline_items if item.area_cluster]
        route_snapshot = self.map_provider.route_summary(area_clusters)
        weather_snapshot = self.weather_provider.weather_hint(request.location_anchor, rainy=request.weather_sensitive)

        availability = []
        events = []
        for item in option.timeline_items:
            result = self.commerce_provider.check_availability(item.merchant_id, request.time_window, request.party_size)
            events.append(result.event)
            data = dict(result.data)
            availability.append(
                {
                    "merchant_id": item.merchant_id,
                    "merchant_name": item.merchant_name,
                    "available": bool(data.get("available")),
                    "remaining_capacity": data.get("remaining_capacity"),
                    "data_confidence": "seed",
                }
            )

        live_confidence = "live" if (
            route_snapshot.data_confidence == "live" or weather_snapshot.data_confidence == "live"
        ) else ("cache" if route_snapshot.data_confidence == "cache" else "seed")
        degraded = route_snapshot.data_confidence != "live" or weather_snapshot.data_confidence != "live"
        refresh_status = "live_refreshed" if live_confidence == "live" else "seed_estimate"
        refresh_message = (
            "Route/weather refreshed from configured real APIs; commerce remains mock because Meituan API is not authorized."
            if live_confidence == "live"
            else "Real route/weather APIs unavailable or not configured; using seed/cache estimates."
        )

        return {
            "itinerary_id": option.id,
            "status": refresh_status,
            "provider_mode": self.settings.tools.data_mode,
            "data_confidence": live_confidence,
            "route": {
                "provider": route_snapshot.provider,
                "status": route_snapshot.status,
                "message": route_snapshot.message,
            },
            "weather": {
                "provider": weather_snapshot.provider,
                "status": weather_snapshot.status,
                "message": weather_snapshot.message,
            },
            "commerce": {
                "provider": "mock_commerce",
                "status": "seed_estimate",
                "availability": availability,
                "message": "库存和价格为 mock/seed 估算，真实履约需接授权接口后确认。",
            },
            "degraded": degraded,
            "message": refresh_message,
            "tool_events": [event.__dict__ for event in events],
        }

    def sync_provider_data(
        self,
        city: str = "hangzhou",
        keywords: list[str] | None = None,
        area: str | None = None,
    ) -> dict[str, object]:
        sync_live_sources = getattr(self.local_data_provider, "sync_live_sources", None)
        if callable(sync_live_sources):
            result = sync_live_sources(city, keywords=keywords, area=area)
            self._refresh_runtime_catalog(city)
            clusters = self.local_data_provider.list_route_clusters(city)
            templates = self.local_data_provider.list_theme_templates(city)
            return {
                **result,
                "route_clusters": len(clusters),
                "theme_templates": len(templates),
                "commerce_provider": "mock_meituan",
            }

        supplies = self.local_data_provider.list_supplies(city)
        clusters = self.local_data_provider.list_route_clusters(city)
        templates = self.local_data_provider.list_theme_templates(city)
        return {
            "city": city,
            "status": "seed_synced",
            "data_mode": self.settings.tools.data_mode,
            "places": len(supplies),
            "route_clusters": len(clusters),
            "theme_templates": len(templates),
            "message": "当前为 seed/local_db 同步结果；真实 provider 需要配置授权 Key 后接入。",
        }

    def _prepare_theme_poi_candidates(self, theme, request: UserRequest) -> tuple[UserRequest, list[dict[str, str]]]:
        request = self._resolve_origin_with_amap(request)
        seeds = keyword_seeds_for_theme(theme, request)
        expanded = self.keyword_expander.expand(theme.name, seeds, request)
        search_keywords = [item.as_dict() for item in expanded]
        keyword_values = [item.keyword for item in expanded]

        sync_theme_pois = getattr(self.local_data_provider, "sync_theme_pois", None)
        if callable(sync_theme_pois):
            sync_theme_pois(
                "hangzhou",
                keyword_values,
                request.origin_longitude,
                request.origin_latitude,
                request.search_radius_km,
            )
            self._refresh_runtime_catalog("hangzhou")

        self._enrich_theme_candidates_with_mock_profiles("hangzhou")
        preferred_ids = self._preferred_supply_ids(theme, request)
        if preferred_ids:
            constraints = dict(request.hard_constraints)
            constraints["preferred_supply_ids"] = preferred_ids
            request = replace(request, hard_constraints=constraints)
        return request, search_keywords

    def _resolve_origin_with_amap(self, request: UserRequest) -> UserRequest:
        if request.origin_longitude is not None and request.origin_latitude is not None:
            return request
        client = getattr(self.local_data_provider, "amap_client", None)
        if client is None:
            return request
        try:
            poi = client.resolve_location(self.settings.tools.amap_city, request.origin_name or request.location_anchor)
        except Exception:
            return request
        if not poi:
            return request
        location = str(poi.get("location") or "")
        if "," not in location:
            return request
        try:
            longitude_text, latitude_text = location.split(",", 1)
            longitude = float(longitude_text)
            latitude = float(latitude_text)
        except ValueError:
            return request
        return replace(
            request,
            origin_name=str(poi.get("name") or request.origin_name),
            origin_address=str(poi.get("address") or request.origin_address),
            origin_longitude=longitude,
            origin_latitude=latitude,
        )

    def _enrich_theme_candidates_with_mock_profiles(self, city: str) -> None:
        supplies = [
            supply
            for supply in self.local_data_provider.list_supplies(city)
            if supply.matched_keywords or supply.source in {"amap_poi", "amap_theme_poi", "hangzhou_open_data"}
        ][:30]
        enriched = []
        for supply in supplies:
            profile_result = self.commerce_provider.merchant_profile(supply.id, supply.name)
            profile = dict(profile_result.data)
            enriched.append(replace(supply, merchant_profile=profile))
        if enriched:
            self.repository.upsert_supplies(enriched, "mock_meituan_profile")
            self._refresh_runtime_catalog(city)

    def _preferred_supply_ids(self, theme, request: UserRequest) -> list[str]:
        candidates = [
            supply
            for supply in self.local_data_provider.list_supplies("hangzhou")
            if supply.available and (supply.matched_keywords or supply.merchant_profile)
        ][:30]
        return self.itinerary_curator.preferred_supply_ids(theme, request, candidates)

    def _attach_live_context(
        self,
        option: PlanOption,
        request: UserRequest,
        search_keywords: list[dict[str, str]],
    ) -> PlanOption:
        return replace(
            option,
            search_keywords=search_keywords,
            route_plan=self._route_plan_for_option(option, request),
        )

    def _route_plan_for_option(self, option: PlanOption, request: UserRequest) -> dict[str, object]:
        points = [
            {
                "name": request.origin_name,
                "address": request.origin_address,
                "longitude": request.origin_longitude,
                "latitude": request.origin_latitude,
            },
            *[
                {
                    "name": item.merchant_name,
                    "address": item.address,
                    "longitude": item.longitude,
                    "latitude": item.latitude,
                }
                for item in option.timeline_items
            ],
        ]
        legs = []
        total_distance_km = 0.0
        total_duration_minutes = 0
        provider = "seed_route"
        status = "seed"

        for origin, destination in zip(points, points[1:]):
            leg = self._route_leg(origin, destination)
            legs.append(leg)
            total_distance_km += float(leg.get("distance_km") or 0)
            total_duration_minutes += int(leg.get("duration_minutes") or 0)
            if leg.get("provider") == "amap_route":
                provider = "amap_route"
                status = "live"

        total_distance_km = round(total_distance_km, 2)
        return {
            "origin": points[0],
            "legs": legs,
            "total_distance_km": total_distance_km,
            "total_duration_minutes": total_duration_minutes,
            "route_limit_km": request.route_limit_km,
            "route_limit_minutes": request.route_limit_minutes,
            "within_limits": total_distance_km <= request.route_limit_km
            and total_duration_minutes <= request.route_limit_minutes,
            "provider": provider,
            "status": status,
        }

    def _route_leg(self, origin: dict[str, object], destination: dict[str, object]) -> dict[str, object]:
        origin_lng = origin.get("longitude")
        origin_lat = origin.get("latitude")
        dest_lng = destination.get("longitude")
        dest_lat = destination.get("latitude")
        if None in {origin_lng, origin_lat, dest_lng, dest_lat}:
            return {
                "from": origin.get("name"),
                "to": destination.get("name"),
                "distance_km": 0,
                "duration_minutes": 0,
                "mode": "unknown",
                "provider": "seed_route",
                "message": "Missing coordinates; route leg needs AMAP refresh.",
            }

        origin_coord = f"{origin_lng},{origin_lat}"
        destination_coord = f"{dest_lng},{dest_lat}"
        client = getattr(self.map_provider, "client", None)
        if client is not None:
            try:
                payload = client.walking_route(origin_coord, destination_coord)
                path = ((payload.get("route") or {}).get("paths") or [{}])[0]
                distance_km = round(float(path.get("distance") or 0) / 1000, 2)
                duration_minutes = max(1, round(float(path.get("duration") or 0) / 60))
                return {
                    "from": origin.get("name"),
                    "to": destination.get("name"),
                    "distance_km": distance_km,
                    "duration_minutes": duration_minutes,
                    "mode": "walking",
                    "provider": "amap_route",
                    "message": f"AMAP walking leg: {distance_km}km / {duration_minutes}min.",
                }
            except Exception:
                pass

        distance_km = round(
            self._haversine_km(float(origin_lat), float(origin_lng), float(dest_lat), float(dest_lng)),
            2,
        )
        duration_minutes = max(1, round(distance_km / 4.5 * 60))
        return {
            "from": origin.get("name"),
            "to": destination.get("name"),
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "mode": "walking_estimate",
            "provider": "seed_route",
            "message": f"Estimated walking leg: {distance_km}km / {duration_minutes}min.",
        }

    def _haversine_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        radius = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        )
        return 2 * radius * math.asin(math.sqrt(a))

    def chat(self, session_id: str, text: str) -> AgentResponse:
        """简化的聊天方法 - 使用新的对话管理器逻辑"""
        self._ensure_session(session_id)
        self.repository.add_message(session_id, "user", text)

        latest = self.repository.get_latest_planning(session_id)
        partial_request = latest["request"] if latest else None
        
        # 直接规划，不使用旧的 LLM 编排器
        result = self.plan(text, partial_request=partial_request, llm_data={})
        share_cards = [self.render_share_card(option, result.request) for option in result.options]
        self.repository.save_planning_result(session_id, result, share_cards)

        message = self._planning_message(result)
        self.repository.add_message(session_id, "assistant", message)
        
        from activity_agent.domain.models import ToolEvent
        dummy_event = ToolEvent(name="chat", input_summary={"text": text[:120]}, output_summary={}, status="ok", duration_ms=0)
        
        return AgentResponse(
            session_id=session_id,
            intent=result.route.intent,
            scene=result.request.scene,
            message=message,
            request=result.request,
            options=result.options,
            share_cards=share_cards,
            missing_questions=result.missing_questions,
            assumptions=result.assumptions,
            tool_events=[dummy_event],
            degraded=False,
        )

    def select_option(self, session_id: str, option_id: str) -> AgentResponse:
        latest = self._latest_planning_or_raise(session_id)
        option = self._find_option(latest["options"], option_id)
        request = latest["request"]
        self.repository.save_selected_option(session_id, option, request)
        card = self.render_share_card(option, request)
        message = f"已选择“{option.theme_name}”。下一步可以提交朋友反馈，或创建预约草稿。"
        self.repository.add_message(session_id, "assistant", message)
        return AgentResponse(
            session_id=session_id,
            intent=Intent.PLAN,
            scene=request.scene,
            message=message,
            request=request,
            options=[option],
            share_cards=[card],
        )

    def submit_feedback(self, session_id: str, feedback: list[InviteFeedback]) -> AgentResponse:
        latest = self._latest_planning_or_raise(session_id)
        selected = self.repository.get_selected_option(session_id)
        preferred_option, request = selected if selected else (latest["options"][0], latest["request"])
        self.repository.save_feedback(session_id, feedback)
        revised_request, revised_option, notes = self.resolve_feedback(request, feedback, preferred_option.theme_name)
        route = RouteResult(intent=Intent.FEEDBACK, scene=revised_request.scene, confidence=0.9, signals=["invite_feedback"])
        result = PlanningResult(
            route=route,
            request=revised_request,
            missing_questions=[],
            assumptions=notes,
            options=[revised_option],
        )
        share_cards = [self.render_share_card(revised_option, revised_request)]
        self.repository.save_planning_result(session_id, result, share_cards)
        self.repository.save_selected_option(session_id, revised_option, revised_request)
        message = "已根据反馈收敛方案：" + "；".join(notes)
        self.repository.add_message(session_id, "assistant", message)
        return AgentResponse(
            session_id=session_id,
            intent=Intent.FEEDBACK,
            scene=revised_request.scene,
            message=message,
            request=revised_request,
            options=[revised_option],
            share_cards=share_cards,
            assumptions=notes,
        )

    def plan(
        self,
        text: str,
        partial_request: UserRequest | None = None,
        scene_hint: Scene | None = None,
        llm_data: dict[str, Any] | None = None,
    ) -> PlanningResult:
        scene_from_llm = self._scene_from_llm(llm_data)
        route = self.intent_router.route(text, scene_hint=scene_hint or scene_from_llm or (partial_request.scene if partial_request else None))
        request, missing_questions, assumptions = self.context_collector.collect(route, text, partial_request)
        request = self._merge_llm_data(request, llm_data or {})
        request = self._apply_adjustments(text, request)
        themes = self.theme_planner.plan(request)
        request, search_keywords = self._prepare_theme_poi_candidates(themes[0], request)
        options = self.itinerary_composer.compose(themes, request)
        options = [self._attach_live_context(option, request, search_keywords) for option in options]
        return PlanningResult(
            route=route,
            request=request,
            missing_questions=missing_questions,
            assumptions=assumptions,
            options=options,
        )

    def render_share_card(self, option: PlanOption, request: UserRequest) -> str:
        return self.share_card_generator.render(option, request)

    def resolve_feedback(
        self,
        request: UserRequest,
        feedback: list[InviteFeedback],
        preferred_theme_name: str | None = None,
    ) -> tuple[UserRequest, PlanOption, list[str]]:
        return self.feedback_resolver.resolve(request, feedback, preferred_theme_name)

    def create_booking_draft(
        self,
        session_or_option: str | PlanOption,
        option_id_or_request: str | UserRequest | None = None,
        pay_mode: PayMode | None = None,
    ) -> BookingDraft:
        if isinstance(session_or_option, PlanOption):
            if not isinstance(option_id_or_request, UserRequest):
                raise ValueError("The legacy create_booking_draft(option, request) form requires a UserRequest.")
            return self.booking_orchestrator.create_draft(session_or_option, option_id_or_request, pay_mode)

        session_id = session_or_option
        latest = self._latest_planning_or_raise(session_id)
        request = latest["request"]
        option_id = option_id_or_request if isinstance(option_id_or_request, str) else None
        if option_id:
            option = self._find_option(latest["options"], option_id)
        else:
            selected = self.repository.get_selected_option(session_id)
            option = selected[0] if selected else latest["options"][0]

        draft = self.booking_orchestrator.create_draft(option, request, pay_mode)
        self.repository.save_booking_draft(session_id, draft)
        return draft

    def confirm_booking(self, session_id: str, draft_id: str, confirm: bool) -> BookingConfirmation:
        self._ensure_session(session_id)
        draft = self.repository.get_booking_draft(session_id, draft_id)
        if not draft:
            raise ValueError(f"Booking draft not found: {draft_id}")
        confirmation = self.booking_orchestrator.confirm_draft(draft, confirm)
        self.repository.save_booking_confirmation(session_id, confirmation)
        return confirmation

    def create_review(
        self,
        session_or_option: str | PlanOption,
        actual_cost_per_person: int,
        attendance: int,
        ratings: dict[str, float],
        complaints: list[str] | None = None,
    ) -> AfterActionReview:
        if isinstance(session_or_option, PlanOption):
            return self.review_memory.create_review(session_or_option, actual_cost_per_person, attendance, ratings, complaints)

        session_id = session_or_option
        selected = self.repository.get_selected_option(session_id)
        latest = self._latest_planning_or_raise(session_id)
        option = selected[0] if selected else latest["options"][0]
        review = self.review_memory.create_review(option, actual_cost_per_person, attendance, ratings, complaints)
        self.repository.save_review(session_id, review)
        return review

    def _ensure_session(self, session_id: str) -> None:
        if not self.repository.get_session(session_id):
            raise ValueError(f"Session not found: {session_id}")

    def _latest_planning_or_raise(self, session_id: str) -> dict[str, Any]:
        self._ensure_session(session_id)
        latest = self.repository.get_latest_planning(session_id)
        if not latest:
            raise ValueError(f"No planning result found for session: {session_id}")
        return latest

    def _find_option(self, options: list[PlanOption], option_id: str) -> PlanOption:
        try:
            return next(option for option in options if option.id == option_id)
        except StopIteration as exc:
            raise ValueError(f"Plan option not found: {option_id}") from exc

    def _planning_message(self, result: PlanningResult) -> str:
        label = "杭州主题局" if result.request.location_anchor == "hangzhou" else ("约会方案" if result.request.scene == Scene.COUPLE else "组局方案")
        names = " / ".join(option.theme_name for option in result.options)
        return f"我给你配了 {len(result.options)} 个{label}：{names}。"

    def _theme_prompt(self, theme_id: str | None) -> str:
        mapping = {
            "hz_old_town_fireworks": "老城烟火 特色美食 本土底蕴",
            "hz_canal_citywalk": "运河 人文 Citywalk",
            "hz_westlake_easy": "西湖 低体力 打卡",
            "hz_longwu_suburb": "近郊山水 茶山 龙坞",
            "hz_food_tour": "特色美食 小吃 老城烟火",
            "hz_rainy_indoor": "雨天 室内 低体力",
        }
        return mapping.get(str(theme_id or ""), "杭州 老城烟火 特色美食")

    def _scene_from_llm(self, llm_data: dict[str, Any] | None) -> Scene | None:
        if not llm_data or not llm_data.get("scene"):
            return None
        try:
            return Scene(str(llm_data["scene"]))
        except ValueError:
            return None

    def _merge_llm_data(self, request: UserRequest, data: dict[str, Any]) -> UserRequest:
        if not data:
            return request

        hard_constraints = dict(request.hard_constraints)
        hard_constraints.update({key: bool(value) for key, value in dict(data.get("hard_constraints") or {}).items()})

        mood_tags = list(dict.fromkeys([*request.mood_tags, *list(data.get("mood_tags") or [])]))
        experience_tags = list(dict.fromkeys([*request.experience_tags, *list(data.get("experience_tags") or [])]))
        budget = self._safe_int(data.get("budget_per_person"), request.budget_per_person)
        party_size = self._safe_int(data.get("party_size"), request.party_size)

        return replace(
            request,
            time_window=str(data.get("time_window") or request.time_window),
            location_anchor=str(data.get("location_anchor") or request.location_anchor),
            budget_per_person=budget,
            party_size=party_size,
            mood_tags=mood_tags,
            relationship_stage=data.get("relationship_stage") or request.relationship_stage,
            relationship_goal=data.get("relationship_goal") or request.relationship_goal,
            hard_constraints=hard_constraints,
            journey_duration=str(data.get("journey_duration") or request.journey_duration),
            experience_tags=experience_tags,
            planning_effort=str(data.get("planning_effort") or request.planning_effort),
            travel_radius_km=float(data.get("travel_radius_km") or request.travel_radius_km),
            weather_sensitive=bool(data.get("weather_sensitive") or request.weather_sensitive),
            origin_name=str(data.get("origin_name") or request.origin_name),
            origin_address=str(data.get("origin_address") or request.origin_address),
            origin_amap_url=str(data.get("origin_amap_url") or request.origin_amap_url),
            origin_longitude=self._safe_float(data.get("origin_longitude"), request.origin_longitude),
            origin_latitude=self._safe_float(data.get("origin_latitude"), request.origin_latitude),
            search_radius_km=self._safe_float(data.get("search_radius_km"), request.search_radius_km) or 5.0,
            route_limit_km=self._safe_float(data.get("route_limit_km"), request.route_limit_km) or 6.0,
            route_limit_minutes=self._safe_int(data.get("route_limit_minutes"), request.route_limit_minutes),
        )

    def _safe_int(self, value: object, fallback: int) -> int:
        try:
            return int(value) if value is not None else fallback
        except (TypeError, ValueError):
            return fallback

    def _safe_float(self, value: object, fallback: float | None) -> float | None:
        try:
            return float(value) if value is not None else fallback
        except (TypeError, ValueError):
            return fallback

    def _apply_adjustments(self, text: str, request: UserRequest) -> UserRequest:
        normalized = str(text or "")
        constraints = dict(request.hard_constraints)
        budget = request.budget_per_person
        mood_tags = list(request.mood_tags)
        search_radius_km = request.search_radius_km
        route_limit_km = request.route_limit_km
        route_limit_minutes = request.route_limit_minutes

        if "便宜点" in normalized or "预算太高" in normalized:
            constraints["cheaper"] = True
            budget = max(80, int(budget * 0.75))
            mood_tags.append("省钱")
        if "不喝酒" in normalized:
            constraints["no_alcohol"] = True
        if "室内" in normalized:
            constraints["indoor_only"] = True
        if "出片" in normalized or "拍照" in normalized:
            constraints["photo_friendly"] = True
            mood_tags.append("出片")
        if "酒店" in normalized or "过夜" in normalized:
            constraints["hotel_wanted"] = True
        if "礼物" in normalized or "花" in normalized or "蛋糕" in normalized:
            constraints["gift_wanted"] = True
        experience_tags = list(request.experience_tags)
        if "室内" in normalized:
            experience_tags.append("雨天室内")
        if "少走路" in normalized or "不想太累" in normalized:
            experience_tags.append("低体力")
        if "加拍照点" in normalized:
            experience_tags.append("打卡")

        radius_match = re.search(r"(?:周边|附近|半径)\s*(\d+(?:\.\d+)?)\s*公里", normalized)
        route_km_match = re.search(r"(?:路线|全程|总路程|路程)\D{0,8}(\d+(?:\.\d+)?)\s*公里", normalized)
        minutes_match = re.search(r"(\d{1,3})\s*分钟", normalized)
        if radius_match:
            search_radius_km = float(radius_match.group(1))
        if route_km_match:
            route_limit_km = float(route_km_match.group(1))
        if minutes_match:
            route_limit_minutes = int(minutes_match.group(1))

        return replace(
            request,
            budget_per_person=budget,
            mood_tags=list(dict.fromkeys(mood_tags)),
            experience_tags=list(dict.fromkeys(experience_tags)),
            hard_constraints=constraints,
            search_radius_km=search_radius_km,
            travel_radius_km=search_radius_km,
            route_limit_km=route_limit_km,
            route_limit_minutes=route_limit_minutes,
        )

    def chat_with_guidance(self, session_id: str, text: str, scene_hint: Scene | str | None = None) -> AgentResponse:
        """
        带对话引导的聊天接口 - 实现多轮对话流程
        
        1. 先识别用户群体（朋友/情侣）
        2. 多轮交流确定需求
        3. 提供多个方案
        4. 用户选择后自动预约
        """
        self._ensure_session(session_id)

        latest = self.repository.get_latest_planning(session_id)
        partial_request = latest["request"] if latest else None
        hinted_scene = self._coerce_scene(scene_hint)

        ctx, reply_msg, should_continue = self.dialogue_manager.process_input(
            session_id, text, partial_request, hinted_scene
        )

        self.repository.add_message(session_id, "user", text)

        if not should_continue and ctx.state in {DialogueState.READY_TO_PLAN, DialogueState.REFINING_DETAILS}:
            planning_text = self._guided_planning_text(ctx)
            result = self.plan(planning_text, partial_request=partial_request, scene_hint=ctx.scene, llm_data={})
            share_cards = [self.render_share_card(option, result.request) for option in result.options]
            self.repository.save_planning_result(session_id, result, share_cards)
            message = reply_msg + "\n\n" + self._planning_message(result)
            self.repository.add_message(session_id, "assistant", message)
            self.dialogue_manager.mark_options_presented(session_id)
            from activity_agent.domain.models import ToolEvent

            dummy_event = ToolEvent(
                name="guided_chat",
                input_summary={"text": text[:120], "scene_hint": ctx.scene.value if ctx.scene else None},
                output_summary={"options": len(result.options), "state": self.get_conversation_state(session_id)},
                status="ok",
                duration_ms=0,
            )
            return AgentResponse(
                session_id=session_id,
                intent=result.route.intent,
                scene=result.request.scene,
                message=message,
                request=result.request,
                options=result.options,
                share_cards=share_cards,
                missing_questions=result.missing_questions,
                assumptions=result.assumptions,
                tool_events=[dummy_event],
                degraded=False,
            )

        self.repository.add_message(session_id, "assistant", reply_msg)

        return AgentResponse(
            session_id=session_id,
            intent=Intent.PLAN,
            scene=ctx.scene or Scene.FRIENDS,
            message=reply_msg,
            request=partial_request,
            options=[],
            share_cards=[],
            missing_questions=[],
            assumptions=[],
            tool_events=[],
            degraded=False,
        )

    def select_and_book(self, session_id: str, option_id: str) -> tuple[BookingDraft, BookingConfirmation]:
        """
        选择方案并自动完成预约
        
        Returns:
            (booking_draft, booking_confirmation)
        """
        select_response = self.select_option(session_id, option_id)

        draft = self.create_booking_draft(session_id, option_id)
        confirmation = self.confirm_booking(session_id, draft.id, confirm=True)

        self.dialogue_manager.mark_booking(session_id)
        self.dialogue_manager.mark_completed(session_id)

        return draft, confirmation

    def get_conversation_state(self, session_id: str) -> str:
        """获取当前对话状态"""
        ctx = self.dialogue_manager.get_or_create_context(session_id)
        return ctx.state.value

    def get_conversation_payload(self, session_id: str, has_options: bool = False) -> dict[str, object]:
        return self.dialogue_manager.conversation_payload(session_id, has_options)

    def _guided_planning_text(self, ctx: DialogueContext) -> str:
        user_messages = [message["content"] for message in ctx.messages if message.get("role") == "user"]
        scene_text = "情侣约会" if ctx.scene == Scene.COUPLE else "朋友局"
        collected = []
        if ctx.collected_info.get("mood"):
            collected.append("想要" + "、".join(ctx.collected_info["mood"]))
        if ctx.collected_info.get("relationship_stage"):
            collected.append(str(ctx.collected_info["relationship_stage"]))
        if ctx.collected_info.get("relationship_goal"):
            collected.append(str(ctx.collected_info["relationship_goal"]))
        if ctx.collected_info.get("budget"):
            collected.append(f"人均{ctx.collected_info['budget']}")
        if ctx.collected_info.get("time"):
            collected.append(str(ctx.collected_info["time"]))
        if ctx.collected_info.get("location"):
            collected.append(f"从{ctx.collected_info['location']}附近出发")
        if ctx.collected_info.get("search_radius_km"):
            collected.append(f"周边{ctx.collected_info['search_radius_km']}公里")
        if ctx.collected_info.get("route_limit_km"):
            collected.append(f"路线控制在{ctx.collected_info['route_limit_km']}公里")
        if ctx.collected_info.get("route_limit_minutes"):
            collected.append(f"{ctx.collected_info['route_limit_minutes']}分钟内")
        return "，".join([scene_text, "杭州", *collected, *user_messages])

    def _coerce_scene(self, scene_hint: Scene | str | None) -> Scene | None:
        if scene_hint is None:
            return None
        if isinstance(scene_hint, Scene):
            return scene_hint
        try:
            return Scene(str(scene_hint))
        except ValueError:
            return None
