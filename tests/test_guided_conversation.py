import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import ConfirmationStatus, Scene
from backend.main import GuidedChatRequest, guided_chat


class GuidedConversationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ActivityPlanningAgent()

    def test_guided_friends_collects_context_before_cards(self) -> None:
        session = self.agent.start_session()

        first = self.agent.chat_with_guidance(session.id, "朋友局", scene_hint=Scene.FRIENDS)
        second = self.agent.chat_with_guidance(session.id, "想轻松聊聊天，最近有点累")
        third = self.agent.chat_with_guidance(session.id, "人均200")
        distance_prompt = self.agent.chat_with_guidance(session.id, "今晚")
        ready = self.agent.chat_with_guidance(session.id, "默认")

        self.assertEqual(first.options, [])
        self.assertEqual(second.options, [])
        self.assertEqual(third.options, [])
        self.assertEqual(distance_prompt.options, [])
        self.assertIn("集合点默认奥映世纪轩", distance_prompt.message)
        self.assertEqual(len(ready.options), 3)
        self.assertEqual(ready.request.scene, Scene.FRIENDS)
        self.assertEqual(ready.request.budget_per_person, 200)
        self.assertEqual(ready.request.origin_name, "奥映世纪轩")
        self.assertEqual(ready.request.search_radius_km, 5.0)
        self.assertEqual(ready.request.route_limit_km, 6.0)
        self.assertEqual(ready.request.route_limit_minutes, 45)
        self.assertTrue({"聊天", "回血"} & set(ready.request.mood_tags))
        self.assertEqual(self.agent.get_conversation_state(session.id), "awaiting_selection")

    def test_guided_couple_infers_relationship_without_direct_question(self) -> None:
        session = self.agent.start_session()
        messages: list[str] = []

        messages.append(self.agent.chat_with_guidance(session.id, "情侣约会", scene_hint=Scene.COUPLE).message)
        messages.append(self.agent.chat_with_guidance(session.id, "周末想约她出来，有点怕尴尬，想轻松自然一点").message)
        budget_response = self.agent.chat_with_guidance(session.id, "人均300")
        messages.append(budget_response.message)
        time_response = budget_response if budget_response.options else self.agent.chat_with_guidance(session.id, "周六下午")
        ready = time_response if time_response.options else self.agent.chat_with_guidance(session.id, "默认")

        self.assertEqual(len(ready.options), 3)
        self.assertEqual(ready.request.scene, Scene.COUPLE)
        self.assertEqual(ready.request.relationship_stage, "暧昧/追求中")
        self.assertIn(ready.request.relationship_goal, {"降低尴尬", "自然升温"})
        self.assertFalse(any("暧昧/追求中、刚在一起、稳定情侣" in message for message in messages))

    def test_guided_adjustment_regenerates_options_same_turn(self) -> None:
        session = self.agent.start_session()
        self.agent.chat_with_guidance(session.id, "朋友局", scene_hint=Scene.FRIENDS)
        self.agent.chat_with_guidance(session.id, "想拍照出片，杭州本地探索")
        self.agent.chat_with_guidance(session.id, "人均260")
        self.agent.chat_with_guidance(session.id, "周末")
        ready = self.agent.chat_with_guidance(session.id, "默认")
        initial_budget = ready.request.budget_per_person

        adjusted = self.agent.chat_with_guidance(session.id, "便宜点，少走路")

        self.assertEqual(len(adjusted.options), 3)
        self.assertLess(adjusted.request.budget_per_person, initial_budget)
        self.assertIn("低体力", adjusted.request.experience_tags)
        self.assertEqual(self.agent.get_conversation_state(session.id), "awaiting_selection")

    def test_booking_stays_draft_until_user_confirmation(self) -> None:
        session = self.agent.start_session()
        self.agent.chat_with_guidance(session.id, "朋友局", scene_hint=Scene.FRIENDS)
        self.agent.chat_with_guidance(session.id, "想放松回血，杭州本地探索")
        self.agent.chat_with_guidance(session.id, "人均220")
        self.agent.chat_with_guidance(session.id, "今晚")
        ready = self.agent.chat_with_guidance(session.id, "默认")

        draft = self.agent.create_booking_draft(session.id, ready.options[0].id)
        cancelled = self.agent.confirm_booking(session.id, draft.id, confirm=False)
        confirmed = self.agent.confirm_booking(session.id, draft.id, confirm=True)

        self.assertEqual(draft.status, "pending_user_confirmation")
        self.assertTrue(draft.confirmation_required)
        self.assertEqual(cancelled.status, ConfirmationStatus.CANCELLED)
        self.assertFalse(cancelled.order_ids)
        self.assertEqual(confirmed.status, ConfirmationStatus.CONFIRMED)
        self.assertTrue(confirmed.order_ids)

    def test_guided_api_returns_conversation_metadata(self) -> None:
        payload = guided_chat(GuidedChatRequest(message="朋友局", scene_hint="friends"))

        self.assertEqual(payload["conversation"]["scene"], "friends")
        self.assertEqual(payload["conversation"]["state"], "collecting_friends_context")
        self.assertFalse(payload["conversation"]["should_show_options"])
        self.assertEqual(payload["conversation"]["next_step"], "ask_mood")

    def test_guided_context_accepts_custom_location_and_distance(self) -> None:
        session = self.agent.start_session()

        self.agent.chat_with_guidance(session.id, "朋友局", scene_hint=Scene.FRIENDS)
        self.agent.chat_with_guidance(session.id, "想回血")
        self.agent.chat_with_guidance(session.id, "人均180")
        distance_prompt = self.agent.chat_with_guidance(session.id, "今晚")
        ready = self.agent.chat_with_guidance(session.id, "从西湖文化广场出发，周边3公里，路线控制在4公里，40分钟内")

        self.assertEqual(distance_prompt.options, [])
        self.assertEqual(len(ready.options), 3)
        self.assertEqual(ready.request.origin_name, "西湖文化广场")
        self.assertIsNone(ready.request.origin_longitude)
        self.assertEqual(ready.request.search_radius_km, 3.0)
        self.assertEqual(ready.request.route_limit_km, 4.0)
        self.assertEqual(ready.request.route_limit_minutes, 40)


if __name__ == "__main__":
    unittest.main()
