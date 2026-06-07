import unittest

from activity_agent.config import ToolSettings
from activity_agent.providers import HybridLiveDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository


class FakeAmapAroundClient:
    def __init__(self) -> None:
        self.around_calls: list[dict[str, object]] = []

    def search_pois(self, city: str, keywords: str, types: str = "", offset: int = 20, page: int = 1):
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
                    "name": "范围测试烧烤店",
                    "type": "餐饮服务;中餐厅;烧烤",
                    "address": "奥映世纪轩周边",
                    "adname": "萧山区",
                    "location": "120.2430,30.2432",
                    "biz_ext": {"cost": "98"},
                }
            ]
        elif keywords == "桌游":
            pois = [
                {
                    "id": "B0FFUN001",
                    "name": "范围测试桌游馆",
                    "type": "体育休闲服务;休闲场所;游戏厅",
                    "address": "奥映世纪轩周边",
                    "adname": "萧山区",
                    "location": "120.2440,30.2435",
                    "biz_ext": {"cost": "78"},
                }
            ]
        else:
            pois = []
        return {"status": "1", "pois": pois}


class AmapPoiRangeSearchAcceptanceTest(unittest.TestCase):
    def test_food_and_fun_are_searched_within_user_radius(self) -> None:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapAroundClient()
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
                radius_km=3.0,
            )
            supplies = [supply for supply in provider.list_supplies("hangzhou") if supply.source == "amap_poi"]
            names = {supply.name for supply in supplies}

            self.assertEqual(result["status"], "live_synced")
            self.assertEqual(len(amap_client.around_calls), 2)
            self.assertTrue(all(call["location"] == "120.2425,30.2426" for call in amap_client.around_calls))
            self.assertTrue(all(call["radius_m"] == 3000 for call in amap_client.around_calls))
            self.assertEqual({call["keywords"] for call in amap_client.around_calls}, {"烧烤", "桌游"})
            self.assertIn("范围测试烧烤店", names)
            self.assertIn("范围测试桌游馆", names)
        finally:
            repository.close()


if __name__ == "__main__":
    unittest.main()
