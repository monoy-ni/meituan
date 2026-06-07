import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import BookingReadiness, PlanOption, Scene, TimelineItem, TimelineType, UserRequest
from activity_agent.providers import AmapMapDataProvider


class FakeAmapRouteClient:
    def __init__(self) -> None:
        self.route_calls: list[tuple[str, str]] = []

    def walking_route(self, origin: str, destination: str):
        self.route_calls.append((origin, destination))
        return {"status": "1", "route": {"paths": [{"distance": "1200", "duration": "900"}]}}


def _item(name: str, lng: float, lat: float, index: int) -> TimelineItem:
    return TimelineItem(
        type=TimelineType.DINING if index == 1 else TimelineType.ACTIVITY,
        merchant_id=f"merchant_{index}",
        merchant_name=name,
        start_time="18:30",
        end_time="19:30",
        booking_required=True,
        price_estimate=88,
        why_this_fits=f"{name} 适合当前主题。",
        booking_modes=["reservation"],
        address=f"{name}地址",
        longitude=lng,
        latitude=lat,
    )


class AmapRoutePlanningAcceptanceTest(unittest.TestCase):
    def test_route_plan_uses_amap_walking_route_for_each_leg(self) -> None:
        agent = ActivityPlanningAgent()
        fake_client = FakeAmapRouteClient()
        agent.map_provider = AmapMapDataProvider(fake_client, agent.repository)
        request = UserRequest(
            scene=Scene.FRIENDS,
            time_window="today 18:30-23:30",
            location_anchor="奥映世纪轩",
            budget_per_person=220,
            party_size=4,
            route_limit_km=4.0,
            route_limit_minutes=40,
        )
        option = PlanOption(
            id="route-option",
            theme_name="路径规划验收局",
            emotional_hook="用真实路径把每一站串起来。",
            timeline_items=[
                _item("第一站餐厅", 120.2500, 30.2450, 1),
                _item("第二站游乐", 120.2600, 30.2500, 2),
            ],
            estimated_cost_per_person=176,
            total_distance=0,
            booking_readiness=BookingReadiness.NEEDS_CONFIRMATION,
            replaceable_slots=[],
            risk_notes=[],
            actions=[],
            add_ons=[],
        )

        route_plan = agent._route_plan_for_option(option, request)

        self.assertEqual(len(fake_client.route_calls), 2)
        self.assertEqual(route_plan["provider"], "amap_route")
        self.assertEqual(route_plan["status"], "live")
        self.assertEqual(len(route_plan["legs"]), 2)
        self.assertEqual(route_plan["total_distance_km"], 2.4)
        self.assertEqual(route_plan["total_duration_minutes"], 30)
        self.assertEqual(route_plan["route_limit_km"], 4.0)
        self.assertEqual(route_plan["route_limit_minutes"], 40)
        self.assertTrue(route_plan["within_limits"])


if __name__ == "__main__":
    unittest.main()
