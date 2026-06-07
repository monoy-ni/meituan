import json
import unittest
from dataclasses import replace

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import PayMode, Scene, TimelineType
from activity_agent.modules.experience_card_designer import ThemedOutingDesigner
from activity_agent.tools.mock_meituan import MockMeituanToolClient
from backend.main import _option_payload


class FakeDesignerLLM:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def complete(self, messages):
        return self.payload


class CountingMeituanClient(MockMeituanToolClient):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    def check_availability(self, merchant_id: str, time_window: str, party_size: int):
        self.events.append("check_availability")
        return super().check_availability(merchant_id, time_window, party_size)

    def create_booking_hold(self, items: list[dict[str, object]]):
        self.events.append("create_booking_hold")
        return super().create_booking_hold(items)

    def create_aa_draft(self, total: int, party_size: int, mode: str):
        self.events.append("create_aa_draft")
        return super().create_aa_draft(total, party_size, mode)


class SpyExperienceDesigner:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def design(self, option, request):
        self.events.append("design_experience_card")
        first = option.timeline_items[0]
        return {
            "designer": "themed-outing-designer" if request.scene == Scene.FRIENDS else "couple-date-designer",
            "title": option.theme_name,
            "theme_line": option.emotional_hook,
            "vibe_tags": ["兜底"],
            "play_style": option.route_story or option.emotional_hook,
            "flow": [
                {
                    "merchant_id": first.merchant_id,
                    "merchant_name": first.merchant_name,
                    "time": f"{first.start_time}-{first.end_time}",
                    "role": "兜底开场",
                    "experience": first.why_this_fits,
                }
            ],
            "signature_moments": ["确认玩法卡先生成"],
            "host_tips": ["确认后再预约"],
            "booking_note": "仅生成待确认草稿；用户确认前不会支付或下不可逆订单。",
        }


class ExperienceCardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ActivityPlanningAgent()

    def test_friends_plan_includes_themed_outing_card(self) -> None:
        result = self.agent.plan("今晚下班回血局，4个人，人均220")
        option = result.options[0]
        card = option.experience_card

        self.assertEqual(result.request.scene, Scene.FRIENDS)
        self.assertEqual(card["designer"], "themed-outing-designer")
        self.assertTrue(card["title"])
        self.assertTrue(card["play_style"])
        self.assertTrue(card["flow"])
        self.assertTrue(card["host_tips"])
        self.assertIn("不会支付", card["booking_note"])

    def test_couple_warmup_card_is_low_pressure_and_no_hotel(self) -> None:
        result = self.agent.plan("想约TA出来，怕尴尬，周末下午，人均300")
        option = result.options[0]
        card = option.experience_card

        self.assertEqual(result.request.scene, Scene.COUPLE)
        self.assertEqual(card["designer"], "couple-date-designer")
        self.assertTrue({"低压力", "自然互动", "安全感"} & set(card["vibe_tags"]))
        self.assertFalse(any(item.type == TimelineType.HOTEL for item in option.timeline_items))
        self.assertIn("默认不安排酒店", json.dumps(card, ensure_ascii=False))

    def test_couple_anniversary_card_uses_ritual_language(self) -> None:
        result = self.agent.plan("纪念日想安排花和蛋糕，预算人均700")
        card = result.options[0].experience_card
        text = json.dumps(card, ensure_ascii=False)

        self.assertEqual(card["designer"], "couple-date-designer")
        self.assertIn("仪式", text)
        self.assertIn("确认前不会", card["booking_note"])

    def test_designer_rejects_llm_hallucinated_merchant_ids(self) -> None:
        result = self.agent.plan("今晚下班回血局，4个人，人均220")
        bad_payload = json.dumps(
            {
                "designer": "themed-outing-designer",
                "title": "编造局",
                "theme_line": "看起来很完整",
                "vibe_tags": ["编造"],
                "play_style": "错误地引用不存在的商户",
                "flow": [
                    {
                        "merchant_id": "made_up_merchant",
                        "merchant_name": "不存在的店",
                        "time": "18:30-19:00",
                        "role": "假开场",
                        "experience": "这个商户不在候选里",
                    }
                ],
                "signature_moments": ["错误"],
                "host_tips": ["错误"],
                "booking_note": "确认前不会支付",
            },
            ensure_ascii=False,
        )

        card = ThemedOutingDesigner(FakeDesignerLLM(bad_payload)).design(result.options[0], result.request)
        allowed_ids = {item.merchant_id for item in result.options[0].timeline_items}

        self.assertEqual(card["designer"], "themed-outing-designer")
        self.assertTrue(all(item["merchant_id"] in allowed_ids for item in card["flow"]))

    def test_booking_guard_generates_card_before_mock_meituan_calls(self) -> None:
        events: list[str] = []
        agent = ActivityPlanningAgent(tool_client=CountingMeituanClient(events))
        result = agent.plan("今晚下班回血局，4个人，人均220")

        self.assertTrue(result.options[0].experience_card)
        self.assertEqual(events, [])

        old_option = replace(result.options[0], experience_card={})
        agent.experience_card_designer = SpyExperienceDesigner(events)
        draft = agent.create_booking_draft(old_option, result.request, PayMode.AA_PREPAY)

        self.assertEqual(events[0], "design_experience_card")
        self.assertIn("check_availability", events)
        self.assertIn("create_booking_hold", events)
        self.assertTrue(draft.confirmation_required)

    def test_backend_option_payload_exposes_experience_card(self) -> None:
        result = self.agent.plan("今晚下班回血局，4个人，人均220")
        payload = _option_payload(result.options[0])

        self.assertIn("experience_card", payload)
        self.assertEqual(payload["experience_card"]["designer"], "themed-outing-designer")


if __name__ == "__main__":
    unittest.main()
