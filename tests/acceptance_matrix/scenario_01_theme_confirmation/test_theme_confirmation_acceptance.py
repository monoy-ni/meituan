import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import Scene


class ThemeConfirmationAcceptanceTest(unittest.TestCase):
    def test_ai_confirms_theme_before_generating_options(self) -> None:
        agent = ActivityPlanningAgent()
        session = agent.start_session()

        first = agent.chat_with_guidance(session.id, "今晚想出去玩")
        self.assertEqual(first.options, [])
        self.assertEqual(agent.get_conversation_payload(session.id)["next_step"], "choose_scene")

        second = agent.chat_with_guidance(session.id, "和朋友")
        self.assertEqual(second.options, [])
        self.assertEqual(second.scene, Scene.FRIENDS)

        mood = agent.chat_with_guidance(session.id, "想放松回血")
        self.assertEqual(mood.options, [])

        third = agent.chat_with_guidance(session.id, "人均200")
        self.assertEqual(third.options, [])

        distance_prompt = agent.chat_with_guidance(session.id, "今晚")
        self.assertEqual(distance_prompt.options, [])
        self.assertIn("集合点默认奥映世纪轩", distance_prompt.message)

        ready = agent.chat_with_guidance(session.id, "默认")

        self.assertEqual(ready.request.scene, Scene.FRIENDS)
        self.assertEqual(ready.request.budget_per_person, 200)
        self.assertEqual(ready.request.origin_name, "奥映世纪轩")
        self.assertEqual(ready.request.search_radius_km, 5.0)
        self.assertEqual(ready.request.route_limit_km, 6.0)
        self.assertEqual(ready.request.route_limit_minutes, 45)
        self.assertEqual(len(ready.options), 3)
        self.assertTrue(all(option.search_keywords for option in ready.options))
        self.assertEqual(agent.get_conversation_state(session.id), "awaiting_selection")


if __name__ == "__main__":
    unittest.main()
