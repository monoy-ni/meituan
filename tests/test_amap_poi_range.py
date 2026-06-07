import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.providers import AmapMapDataProvider, HybridLiveDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository


class FakeAmapRangeClient:
    def __init__(self) -> None:
        self.poi_calls = []
        self.around_calls = []

    def search_pois(self, city: str, keywords: str, types: str = "", offset: int = 20, page: int = 1):
        self.poi_calls.append(
            {"city": city, "keywords": keywords, "types": types, "offset": offset, "page": page}
        )
        return {"status": "1", "pois": []}

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

        if keywords == "烧烤":
            pois = [
                {
                    "id": "B0FFOOD001",
                    "name": "测试烧烤店",
                    "type": "餐饮服务;中餐厅;烧烤",
                    "typecode": "050100",
                    "address": "奥映世纪轩周边",
                    "adname": "萧山区",
                    "location": "120.2430,30.2432",
                    "biz_ext": {"cost": "98"},
                }
            ]
        elif keywords in {"桌游", "KTV", "酒吧"}:
            pois = [
                {
                    "id": f"B0FFUN{keywords}",
                    "name": f"测试{keywords}馆",
                    "type": "体育休闲服务;休闲场所;游戏厅",
                    "typecode": "080300",
                    "address": "奥映世纪轩周边",
                    "adname": "萧山区",
                    "location": "120.2440,30.2435",
                    "biz_ext": {"cost": "78"},
                }
            ]
        else:
            pois = []

        return {"status": "1", "pois": pois}

    def walking_route(self, origin: str, destination: str):
        return {"status": "1", "route": {"paths": [{"distance": "1800", "duration": "1200"}]}}


class AmapPoiRangeTest(unittest.TestCase):
    def test_provider_searches_food_and_fun_within_user_radius(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapRangeClient()
            provider = HybridLiveDataProvider(
                repository,
                ToolSettings(data_mode="hybrid", amap_city="330100"),
                amap_client=amap_client,
            )

            result = provider.sync_theme_pois(
                city="hangzhou",
                keywords=["烧烤", "桌游"],
                origin_longitude=120.2425,
                origin_latitude=30.2426,
                radius_km=5.0,
            )

            live_supplies = [supply for supply in provider.list_supplies("hangzhou") if supply.source == "amap_poi"]
            names = {supply.name for supply in live_supplies}

            self.assertEqual(result["status"], "live_synced")
            self.assertEqual(len(amap_client.around_calls), 2)
            self.assertTrue(all(call["location"] == "120.2425,30.2426" for call in amap_client.around_calls))
            self.assertTrue(all(call["radius_m"] == 5000 for call in amap_client.around_calls))
            self.assertTrue(all(call["city"] == "330100" for call in amap_client.around_calls))
            self.assertIn("测试烧烤店", names)
            self.assertIn("测试桌游馆", names)
        finally:
            repository.close()

    def test_agent_passes_search_radius_into_amap_around_chain(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapRangeClient()
            settings = AgentSettings(
                llm=LLMSettings(api_key=None),
                storage=StorageSettings(path=":memory:"),
                tools=ToolSettings(data_mode="hybrid", map_provider="amap", amap_api_key="fake", amap_city="330100"),
            )
            agent = ActivityPlanningAgent(settings=settings, repository=repository)
            agent.local_data_provider = HybridLiveDataProvider(repository, settings.tools, amap_client=amap_client)
            agent.map_provider = AmapMapDataProvider(amap_client, repository)
            agent._refresh_runtime_catalog("hangzhou")

            session = agent.start_session()
            response = agent.generate_itineraries(
                session_id=session.id,
                city="hangzhou",
                message="周边5公里，想和朋友找烧烤和能玩的地方",
                search_radius_km=5.0,
                experience_tags=["美食", "游乐"],
            )

            searched_keywords = {call["keywords"] for call in amap_client.around_calls}

            self.assertEqual(response.request.search_radius_km, 5.0)
            self.assertGreaterEqual(len(amap_client.around_calls), 2)
            self.assertTrue(searched_keywords & {"烧烤", "小吃", "夜宵", "咖啡", "甜品"})
            self.assertTrue(searched_keywords & {"KTV", "酒吧", "桌游"})
            self.assertTrue(all(call["radius_m"] == 5000 for call in amap_client.around_calls))
            self.assertTrue(response.options[0].search_keywords)
            self.assertEqual(response.options[0].route_plan["origin"]["name"], "奥映世纪轩")
        finally:
            repository.close()


if __name__ == "__main__":
    unittest.main()
