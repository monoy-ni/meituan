import json
import os
import tempfile
import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.data.theme_keyword_seeds import (
    COUPLE_GOAL_KEYWORD_SEEDS,
    COUPLE_STAGE_KEYWORD_SEEDS,
    FRIENDS_THEME_KEYWORD_SEEDS,
    THEME_KEYWORD_SEEDS,
    keyword_seeds_for_theme,
)
from activity_agent.domain import PayMode, Scene, TimelineType
from activity_agent.modules.theme_planner import COUPLE_THEMES, FRIENDS_THEMES
from activity_agent.llm import LLMKeywordExpander
from activity_agent.providers import AmapMapDataProvider, AmapWeatherProvider, HybridLiveDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository


class FakeAmapClient:
    def __init__(self) -> None:
        self.poi_calls = []
        self.around_calls = []
        self.route_calls = []

    def search_pois(self, city: str, keywords: str, types: str = "", offset: int = 20, page: int = 1):
        self.poi_calls.append({"city": city, "keywords": keywords, "types": types, "offset": offset, "page": page})
        return {
            "status": "1",
            "pois": [
                {
                    "id": "B0FFAKE001",
                    "name": "测试茶馆",
                    "type": "餐饮服务;茶艺馆;茶艺馆",
                    "typecode": "050600",
                    "address": "西湖湖滨",
                    "adname": "上城区",
                    "location": "120.1608,30.2557",
                    "biz_ext": {"cost": "88"},
                }
            ],
        }

    def search_pois_around(
        self,
        location: str,
        radius_m: int,
        keywords: str,
        city: str = "",
        types: str = "",
        offset: int = 20,
        page: int = 1,
    ):
        self.around_calls.append(
            {
                "location": location,
                "radius_m": radius_m,
                "keywords": keywords,
                "city": city,
                "types": types,
                "offset": offset,
                "page": page,
            }
        )
        return {
            "status": "1",
            "pois": [
                {
                    "id": "B0FFAKE001",
                    "name": "测试烧烤酒馆",
                    "type": "餐饮服务;中餐厅;烧烤",
                    "typecode": "050100",
                    "address": "奥映世纪轩周边",
                    "adname": "萧山区",
                    "location": "120.2428,30.2430",
                    "biz_ext": {"cost": "98"},
                }
            ],
        }

    def weather(self, city: str, extensions: str = "base"):
        return {
            "status": "1",
            "lives": [
                {
                    "city": "杭州市",
                    "weather": "多云",
                    "temperature": "26",
                    "humidity": "61",
                    "winddirection": "东",
                    "windpower": "3",
                    "reporttime": "2026-06-07 15:00:00",
                }
            ],
        }

    def walking_route(self, origin: str, destination: str):
        self.route_calls.append((origin, destination))
        return {
            "status": "1",
            "route": {
                "paths": [
                    {
                        "distance": "2400",
                        "duration": "1800",
                    }
                ]
            },
        }


class FakeKeywordLLM:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def complete(self, messages):
        return self.payload


class HangzhouItineraryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ActivityPlanningAgent()

    def test_old_town_zero_effort_request_returns_closed_loop(self) -> None:
        result = self.agent.plan("今天没目标，不想查攻略，想体验杭州老城烟火，人均200")
        option = result.options[0]
        item_types = {item.type for item in option.timeline_items}

        self.assertEqual(result.request.location_anchor, "hangzhou")
        self.assertEqual(option.theme_name, "杭州老城烟火半日局")
        self.assertIn(TimelineType.DINING, item_types)
        self.assertIn(TimelineType.ACTIVITY, item_types)
        self.assertTrue({TimelineType.CHECKIN, TimelineType.RELAX} & item_types)
        self.assertTrue(option.route_story)
        self.assertTrue(option.checkin_points)

    def test_suburb_low_effort_request_prioritizes_longwu_with_weather_fallback(self) -> None:
        result = self.agent.plan("周末想去杭州近郊山水，不想太累")
        option = result.options[0]

        self.assertEqual(option.theme_name, "龙坞茶山近郊局")
        self.assertNotEqual(option.effort_level, "高")
        self.assertTrue(any("下雨" in fallback for fallback in option.fallbacks))
        self.assertTrue(any("湘湖" in fallback or "西溪" in fallback for fallback in option.fallbacks))

    def test_rainy_hangzhou_request_prefers_indoor_low_effort_theme(self) -> None:
        result = self.agent.plan("下雨，想有杭州特色，别太远")
        option = result.options[0]
        names = [item.merchant_name for item in option.timeline_items]

        self.assertTrue(result.request.weather_sensitive)
        self.assertEqual(option.theme_name, "雨天室内低耗局")
        self.assertFalse(any("茶山" in name or "夜景" in name for name in names))
        self.assertTrue(any("天气" in note for note in option.risk_notes))

    def test_canal_humanities_request_returns_canal_route(self) -> None:
        result = self.agent.plan("想走运河，有点人文，再吃点特色")
        option = result.options[0]

        self.assertEqual(option.theme_name, "运河人文 Citywalk")
        self.assertTrue(all(item.area_cluster == "canal_qiaoxi" for item in option.timeline_items))
        self.assertIn("运河", option.route_story)

    def test_low_budget_keeps_full_loop_with_cheaper_supplies(self) -> None:
        result = self.agent.plan("杭州特色美食，人均80，便宜点，不想查攻略")
        option = result.options[0]
        item_types = {item.type for item in option.timeline_items}

        self.assertLessEqual(option.estimated_cost_per_person, 80)
        self.assertGreaterEqual(len(option.timeline_items), 3)
        self.assertIn(TimelineType.DINING, item_types)
        self.assertIn(TimelineType.ACTIVITY, item_types)
        self.assertTrue({TimelineType.CHECKIN, TimelineType.RELAX} & item_types)

    def test_no_map_api_key_degrades_to_seed_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = AgentSettings(
                llm=LLMSettings(api_key=None),
                storage=StorageSettings(path=os.path.join(tmp, "agent.sqlite3")),
                tools=ToolSettings(data_mode="seed", map_provider="amap", amap_api_key=None),
            )
            agent = ActivityPlanningAgent(settings=settings)
            try:
                session = agent.start_session()
                response = agent.generate_itineraries(session.id, theme_id="hz_canal_citywalk")
                refreshed = agent.refresh_itinerary(session.id, response.options[0].id)

                self.assertEqual(refreshed["status"], "seed_estimate")
                self.assertIn(refreshed["data_confidence"], {"seed", "cache"})
                self.assertEqual(refreshed["commerce"]["status"], "seed_estimate")
                self.assertIn("seed", refreshed["message"])
            finally:
                agent.close()

    def test_theme_seed_maps_recovery_theme_to_tight_keywords(self) -> None:
        self.assertEqual(THEME_KEYWORD_SEEDS["下班兄弟回血局"], ["KTV", "烧烤", "酒吧"])
        self.assertEqual(FRIENDS_THEME_KEYWORD_SEEDS["下班兄弟回血局"], ["KTV", "烧烤", "酒吧"])

    def test_friend_and_couple_keyword_seed_tables_are_scene_specific(self) -> None:
        friend_theme = next(theme for theme in FRIENDS_THEMES if theme.id == "friends_recovery")
        friend_request = self.agent.plan("下班兄弟回血局").request

        self.assertEqual(keyword_seeds_for_theme(friend_theme, friend_request)[:3], ["KTV", "烧烤", "酒吧"])
        self.assertNotIn("轻手作", keyword_seeds_for_theme(friend_theme, friend_request))

        warmup_theme = next(theme for theme in COUPLE_THEMES if theme.id == "couple_warmup")
        warmup_request = self.agent.plan("想约她第一次见面，怕尴尬", scene_hint=Scene.COUPLE).request
        warmup_seeds = keyword_seeds_for_theme(warmup_theme, warmup_request)

        self.assertEqual(COUPLE_STAGE_KEYWORD_SEEDS["暧昧/追求中"], ["咖啡", "甜品", "轻手作"])
        self.assertTrue({"咖啡", "甜品", "轻手作"} <= set(warmup_seeds))

        memory_theme = next(theme for theme in COUPLE_THEMES if theme.id == "couple_memory")
        anniversary_request = self.agent.plan("纪念日想制造仪式感，安排约会", scene_hint=Scene.COUPLE).request
        anniversary_seeds = keyword_seeds_for_theme(memory_theme, anniversary_request)

        self.assertEqual(COUPLE_GOAL_KEYWORD_SEEDS["制造仪式感"], ["西餐", "花店", "蛋糕"])
        self.assertTrue({"西餐", "花店", "蛋糕"} <= set(anniversary_seeds))

    def test_llm_keyword_expander_accepts_related_keywords_and_rejects_unrelated(self) -> None:
        request = self.agent.plan("下班兄弟回血局").request
        valid_payload = json.dumps(
            {
                "keywords": [
                    {"keyword": "量贩KTV", "intent_type": "activity", "reason": "唱歌回血"},
                    {"keyword": "烤肉", "intent_type": "dining", "reason": "补充能量"},
                    {"keyword": "精酿酒吧", "intent_type": "nightlife", "reason": "收尾放松"},
                ]
            },
            ensure_ascii=False,
        )
        expanded = LLMKeywordExpander(FakeKeywordLLM(valid_payload)).expand(
            "下班兄弟回血局",
            ["KTV", "烧烤", "酒吧"],
            request,
        )
        self.assertEqual([item.keyword for item in expanded], ["量贩KTV", "烤肉", "精酿酒吧"])

        invalid_payload = json.dumps(
            {"keywords": [{"keyword": "股票开户", "intent_type": "other", "reason": "无关"}]},
            ensure_ascii=False,
        )
        fallback = LLMKeywordExpander(FakeKeywordLLM(invalid_payload)).expand(
            "下班兄弟回血局",
            ["KTV", "烧烤", "酒吧"],
            request,
        )
        self.assertEqual([item.keyword for item in fallback], ["KTV", "烧烤", "酒吧"])

    def test_amap_route_and_weather_providers_use_live_payloads(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapClient()
            route = AmapMapDataProvider(amap_client, repository).route_summary(
                ["hefang_old_town", "canal_qiaoxi"]
            )
            weather = AmapWeatherProvider(amap_client, "330100").weather_hint("hangzhou")

            self.assertEqual(route.status, "live")
            self.assertEqual(route.data_confidence, "live")
            self.assertIn("AMAP walking route", route.message)
            self.assertEqual(weather.status, "live")
            self.assertEqual(weather.data_confidence, "live")
            self.assertIn("AMAP live weather", weather.message)
            self.assertEqual(len(amap_client.route_calls), 1)
        finally:
            repository.close()

    def test_hybrid_provider_syncs_amap_pois_into_catalog(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            settings = ToolSettings(
                data_mode="hybrid",
                amap_city="330100",
                amap_poi_keywords="茶馆",
            )
            provider = HybridLiveDataProvider(repository, settings, amap_client=FakeAmapClient())

            result = provider.sync_live_sources("hangzhou", keywords=["茶馆"])
            live_supplies = [supply for supply in provider.list_supplies("hangzhou") if supply.source == "amap_poi"]

            self.assertEqual(result["status"], "live_synced")
            self.assertEqual(result["sources"]["amap_poi"]["places"], 1)
            self.assertEqual(len(live_supplies), 1)
            self.assertEqual(live_supplies[0].data_confidence, "live")
            self.assertEqual(live_supplies[0].source_id, "B0FFAKE001")
        finally:
            repository.close()

    def test_theme_poi_sync_uses_amap_around_and_merges_matched_keywords(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapClient()
            settings = ToolSettings(data_mode="hybrid", amap_city="330100")
            provider = HybridLiveDataProvider(repository, settings, amap_client=amap_client)

            result = provider.sync_theme_pois(
                city="hangzhou",
                keywords=["烧烤", "酒吧"],
                origin_longitude=120.2425,
                origin_latitude=30.2426,
                radius_km=5.0,
            )
            live_supplies = [supply for supply in provider.list_supplies("hangzhou") if supply.source == "amap_poi"]

            self.assertEqual(result["status"], "live_synced")
            self.assertEqual(len(amap_client.around_calls), 2)
            self.assertEqual(amap_client.around_calls[0]["radius_m"], 5000)
            self.assertEqual(amap_client.around_calls[0]["city"], "330100")
            self.assertEqual(len(live_supplies), 1)
            self.assertEqual(live_supplies[0].matched_keywords, ["烧烤", "酒吧"])
            self.assertEqual(live_supplies[0].longitude, 120.2428)
            self.assertEqual(live_supplies[0].latitude, 30.2430)
        finally:
            repository.close()

    def test_agent_plan_attaches_keyword_trace_and_route_plan(self) -> None:
        result = self.agent.plan("下班兄弟回血局")
        option = result.options[0]

        self.assertTrue(option.search_keywords)
        self.assertEqual([item["keyword"] for item in option.search_keywords[:3]], ["KTV", "烧烤", "酒吧"])
        self.assertEqual(option.route_plan["origin"]["name"], "奥映世纪轩")
        self.assertEqual(option.route_plan["route_limit_km"], 6.0)
        self.assertEqual(option.route_plan["route_limit_minutes"], 45)
        self.assertEqual(len(option.route_plan["legs"]), len(option.timeline_items))

    def test_couple_flow_uses_same_keyword_expansion_and_amap_around_search(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapClient()
            settings = AgentSettings(
                llm=LLMSettings(api_key=None),
                storage=StorageSettings(path=":memory:"),
                tools=ToolSettings(data_mode="hybrid", map_provider="amap", amap_api_key="fake", amap_city="330100"),
            )
            agent = ActivityPlanningAgent(settings=settings, repository=repository)
            provider = HybridLiveDataProvider(repository, settings.tools, amap_client=amap_client)
            agent.local_data_provider = provider
            agent.map_provider = AmapMapDataProvider(amap_client, repository)
            agent._refresh_runtime_catalog("hangzhou")

            result = agent.plan("想约她第一次见面，怕尴尬，周边5公里", scene_hint=Scene.COUPLE)
            keywords = [call["keywords"] for call in amap_client.around_calls]

            self.assertEqual(result.request.scene, Scene.COUPLE)
            self.assertTrue({"咖啡", "甜品", "轻手作"} <= set(keywords))
            self.assertTrue(all(call["location"] == "120.2425,30.2426" for call in amap_client.around_calls))
            self.assertTrue(all(call["radius_m"] == 5000 for call in amap_client.around_calls))
            self.assertTrue(all(call["city"] == "330100" for call in amap_client.around_calls))
            self.assertTrue(result.options[0].search_keywords)
            self.assertTrue(result.options[0].route_plan["legs"])
        finally:
            repository.close()

    def test_booking_draft_stays_safe_before_confirmation(self) -> None:
        result = self.agent.plan("杭州老城烟火局，人均200，不想查攻略")
        draft = self.agent.create_booking_draft(result.options[0], result.request, PayMode.AA_PREPAY)

        self.assertTrue(draft.confirmation_required)
        self.assertEqual(draft.status, "pending_user_confirmation")
        self.assertIn("不会未经授权支付", draft.safety_notice)
        self.assertEqual(draft.data_confidence, "seed")


if __name__ == "__main__":
    unittest.main()
