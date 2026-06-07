import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.providers import AmapWebServiceClient


class FakeHTTPClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_json(self, url: str, params: dict[str, object] | None = None, headers: dict[str, str] | None = None):
        self.calls.append({"url": url, "params": params or {}, "headers": headers or {}})
        return {
            "status": "1",
            "province": "浙江省",
            "city": "杭州市",
            "adcode": "330100",
            "rectangle": "120.0,30.0;120.4,30.4",
        }


class LocationAmapIPDefaultAcceptanceTest(unittest.TestCase):
    def test_amap_ip_location_client_is_mockable(self) -> None:
        http = FakeHTTPClient()
        client = AmapWebServiceClient("fake-amap-key", http_client=http)

        payload = client.ip_location("101.68.1.1")

        self.assertEqual(payload["city"], "杭州市")
        self.assertEqual(len(http.calls), 1)
        call = http.calls[0]
        self.assertTrue(str(call["url"]).endswith("/ip"))
        self.assertEqual(call["params"]["ip"], "101.68.1.1")
        self.assertEqual(call["params"]["output"], "JSON")
        self.assertEqual(call["params"]["key"], "fake-amap-key")

    def test_default_origin_is_used_when_user_does_not_provide_location(self) -> None:
        result = ActivityPlanningAgent().plan("朋友局，想放松回血，人均180，今晚")
        request = result.request

        self.assertEqual(request.origin_name, "奥映世纪轩")
        self.assertEqual(request.origin_address, "民祥路与平澜路交汇处(地铁6号线丰北站C出口)")
        self.assertEqual(request.origin_amap_url, "https://surl.amap.com/4sRsg3c1oa7b")
        self.assertEqual(request.origin_longitude, 120.2425)
        self.assertEqual(request.origin_latitude, 30.2426)
        self.assertEqual(request.search_radius_km, 5.0)


if __name__ == "__main__":
    unittest.main()
