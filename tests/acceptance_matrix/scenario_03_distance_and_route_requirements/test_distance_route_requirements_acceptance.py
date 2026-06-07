import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import Scene


class DistanceRouteRequirementsAcceptanceTest(unittest.TestCase):
    def test_guided_chat_collects_search_radius_and_route_limits(self) -> None:
        agent = ActivityPlanningAgent()
        session = agent.start_session()

        agent.chat_with_guidance(session.id, "朋友局", scene_hint=Scene.FRIENDS)
        agent.chat_with_guidance(session.id, "想回血，轻松聊聊天")
        agent.chat_with_guidance(session.id, "人均180")
        prompt = agent.chat_with_guidance(session.id, "今晚")

        self.assertIn("搜索范围默认周边 5km", prompt.message)
        self.assertIn("整体路线目标 6km 或 45min 内", prompt.message)

        ready = agent.chat_with_guidance(
            session.id,
            "从西湖文化广场出发，周边3公里，路线控制在4公里，40分钟内",
        )

        self.assertEqual(len(ready.options), 3)
        self.assertEqual(ready.request.origin_name, "西湖文化广场")
        self.assertEqual(ready.request.search_radius_km, 3.0)
        self.assertEqual(ready.request.route_limit_km, 4.0)
        self.assertEqual(ready.request.route_limit_minutes, 40)
        self.assertTrue(ready.options[0].route_plan)
        self.assertEqual(ready.options[0].route_plan["route_limit_km"], 4.0)
        self.assertEqual(ready.options[0].route_plan["route_limit_minutes"], 40)


if __name__ == "__main__":
    unittest.main()
