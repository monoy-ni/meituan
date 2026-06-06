import os
import tempfile
import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.domain import ConfirmationStatus, FeedbackStatus, InviteFeedback, PayMode, Scene, TimelineType
from activity_agent.llm import MockLLMClient, OpenAICompatibleLLMClient


class InvalidJSONLLMClient:
    def complete(self, messages):
        return "not-json"


class MVPSDKTest(unittest.TestCase):
    def settings_for(self, path: str) -> AgentSettings:
        return AgentSettings(
            llm=LLMSettings(api_key=None),
            storage=StorageSettings(path=path),
            tools=ToolSettings(mode="mock"),
        )

    def test_env_settings_load_openai_compatible_config(self) -> None:
        old = dict(os.environ)
        try:
            os.environ["ACTIVITY_AGENT_LLM_BASE_URL"] = "https://llm.example/v1"
            os.environ["ACTIVITY_AGENT_LLM_API_KEY"] = "test-key"
            os.environ["ACTIVITY_AGENT_LLM_MODEL"] = "test-model"
            os.environ["ACTIVITY_AGENT_LLM_TEMPERATURE"] = "0.4"
            os.environ["ACTIVITY_AGENT_LLM_TIMEOUT_SECONDS"] = "9"
            os.environ["ACTIVITY_AGENT_STORAGE_PATH"] = "./tmp-agent.sqlite3"
            os.environ["ACTIVITY_AGENT_TOOL_MODE"] = "mock"

            settings = AgentSettings.from_env()

            self.assertEqual(settings.llm.base_url, "https://llm.example/v1")
            self.assertEqual(settings.llm.api_key, "test-key")
            self.assertEqual(settings.llm.model, "test-model")
            self.assertEqual(settings.llm.temperature, 0.4)
            self.assertEqual(settings.llm.timeout_seconds, 9)
            self.assertEqual(settings.storage.path, "./tmp-agent.sqlite3")
            self.assertEqual(settings.tools.mode, "mock")
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_openai_client_requires_api_key_for_real_calls(self) -> None:
        client = OpenAICompatibleLLMClient(LLMSettings(api_key=None))

        with self.assertRaises(Exception):
            client.complete([{"role": "user", "content": "hi"}])

    def test_invalid_llm_json_falls_back_to_rules_and_marks_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "agent.sqlite3")
            agent = ActivityPlanningAgent(settings=self.settings_for(path), llm_client=InvalidJSONLLMClient())
            try:
                session = agent.start_session("u1")

                response = agent.chat(session.id, "今晚有点无聊，想叫朋友出来")

                self.assertTrue(response.degraded)
                self.assertEqual(response.scene, Scene.FRIENDS)
                self.assertEqual(len(response.options), 3)
                self.assertEqual(response.tool_events[0].status, "error")
            finally:
                agent.close()

    def test_session_persists_plans_and_booking_drafts_across_agent_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "agent.sqlite3")
            settings = self.settings_for(path)
            agent = ActivityPlanningAgent(settings=settings, llm_client=MockLLMClient())
            restarted = None
            try:
                session = agent.start_session("u1")
                response = agent.chat(session.id, "今晚有点无聊，想叫朋友出来，预算人均200")
                selected = agent.select_option(session.id, response.options[0].id)
                agent.close()

                restarted = ActivityPlanningAgent(settings=settings, llm_client=MockLLMClient())
                draft = restarted.create_booking_draft(session.id, selected.options[0].id, PayMode.AA_PREPAY)

                self.assertTrue(draft.id.startswith("draft_"))
                self.assertTrue(draft.hold_id.startswith("hold_"))
                self.assertTrue(draft.confirm_token.startswith("confirm_"))
                self.assertTrue(draft.confirmation_required)
                self.assertEqual(draft.status, "pending_user_confirmation")
                self.assertTrue(draft.aa_draft)

                blocked = restarted.confirm_booking(session.id, draft.id, confirm=False)
                self.assertEqual(blocked.status, ConfirmationStatus.CANCELLED)
                self.assertFalse(blocked.order_ids)

                confirmed = restarted.confirm_booking(session.id, draft.id, confirm=True)
                self.assertEqual(confirmed.status, ConfirmationStatus.CONFIRMED)
                self.assertTrue(confirmed.order_ids)
            finally:
                if restarted is not None:
                    restarted.close()
                else:
                    agent.close()

    def test_submit_feedback_persists_revised_lower_budget_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = ActivityPlanningAgent(settings=self.settings_for(os.path.join(tmp, "agent.sqlite3")))
            try:
                session = agent.start_session("u1")
                response = agent.chat(session.id, "周五下班后想找朋友玩，预算人均220，4个人，想回血")
                agent.select_option(session.id, response.options[0].id)
                feedback = [
                    InviteFeedback("小王", FeedbackStatus.JOIN, budget_feedback=180, preference_tags=["聊天"]),
                    InviteFeedback("小李", FeedbackStatus.LATE, time_feedback="20:30后到"),
                    InviteFeedback("小陈", FeedbackStatus.JOIN, dietary_or_boundary_constraints=["不喝酒"]),
                ]

                revised = agent.submit_feedback(session.id, feedback)

                self.assertLessEqual(revised.request.budget_per_person, 180)
                self.assertTrue(revised.request.hard_constraints["no_alcohol"])
                self.assertTrue(revised.request.hard_constraints["partial_allowed"])
                self.assertEqual(len(revised.options), 1)
            finally:
                agent.close()

    def test_couple_hotel_and_gift_create_mock_hotel_and_delivery_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = ActivityPlanningAgent(settings=self.settings_for(os.path.join(tmp, "agent.sqlite3")))
            try:
                session = agent.start_session("u1")
                response = agent.chat(session.id, "纪念日想安排酒店和花，预算人均700")
                option = response.options[0]

                self.assertEqual(response.scene, Scene.COUPLE)
                self.assertTrue(any(item.type == TimelineType.HOTEL for item in option.timeline_items))
                self.assertTrue(any(item.type == TimelineType.GIFT for item in option.timeline_items))

                draft = agent.create_booking_draft(session.id, option.id)
                self.assertTrue(any(item.type == TimelineType.HOTEL for item in draft.items))
                self.assertTrue(any(item.type == TimelineType.GIFT for item in draft.items))
            finally:
                agent.close()


if __name__ == "__main__":
    unittest.main()
