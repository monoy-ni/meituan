import os
import tempfile
import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.domain import PayMode, TimelineType
from activity_agent.providers import AmapMapDataProvider, AmapWeatherProvider, HybridLiveDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository


class FakeAmapClient:
    def __init__(self) -> None:
        self.poi_calls = []
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

    def test_booking_draft_stays_safe_before_confirmation(self) -> None:
        result = self.agent.plan("杭州老城烟火局，人均200，不想查攻略")
        draft = self.agent.create_booking_draft(result.options[0], result.request, PayMode.AA_PREPAY)

        self.assertTrue(draft.confirmation_required)
        self.assertEqual(draft.status, "pending_user_confirmation")
        self.assertIn("不会未经授权支付", draft.safety_notice)
        self.assertEqual(draft.data_confidence, "seed")


if __name__ == "__main__":
    unittest.main()
