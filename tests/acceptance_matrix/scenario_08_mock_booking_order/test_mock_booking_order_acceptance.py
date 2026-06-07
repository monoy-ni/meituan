import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import ConfirmationStatus, PayMode
from activity_agent.tools.mock_meituan import MockMeituanToolClient


class RecordingMeituanClient(MockMeituanToolClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def check_availability(self, merchant_id: str, time_window: str, party_size: int):
        self.calls.append("check_availability")
        return super().check_availability(merchant_id, time_window, party_size)

    def create_booking_hold(self, items: list[dict[str, object]]):
        self.calls.append("create_booking_hold")
        return super().create_booking_hold(items)

    def create_aa_draft(self, total: int, party_size: int, mode: str):
        self.calls.append("create_aa_draft")
        return super().create_aa_draft(total, party_size, mode)

    def confirm_booking(self, hold_id: str, confirm_token: str, items: list[dict[str, object]]):
        self.calls.append("confirm_booking")
        return super().confirm_booking(hold_id, confirm_token, items)


class MockBookingOrderAcceptanceTest(unittest.TestCase):
    def test_mock_meituan_booking_stays_draft_until_user_confirmation(self) -> None:
        meituan = RecordingMeituanClient()
        agent = ActivityPlanningAgent(tool_client=meituan)
        session = agent.start_session()
        response = agent.chat(session.id, "朋友局，今晚下班回血，4个人，人均220")
        option = response.options[0]

        draft = agent.create_booking_draft(session.id, option.id, PayMode.AA_PREPAY)
        cancelled = agent.confirm_booking(session.id, draft.id, confirm=False)
        confirmed = agent.confirm_booking(session.id, draft.id, confirm=True)

        self.assertEqual(draft.status, "pending_user_confirmation")
        self.assertTrue(draft.confirmation_required)
        self.assertIn("不会未经授权支付", draft.safety_notice)
        self.assertTrue(draft.aa_draft)
        self.assertEqual(cancelled.status, ConfirmationStatus.CANCELLED)
        self.assertFalse(cancelled.order_ids)
        self.assertEqual(confirmed.status, ConfirmationStatus.CONFIRMED)
        self.assertTrue(confirmed.order_ids)
        self.assertGreaterEqual(meituan.calls.count("check_availability"), len(option.timeline_items))
        self.assertIn("create_booking_hold", meituan.calls)
        self.assertIn("create_aa_draft", meituan.calls)
        self.assertIn("confirm_booking", meituan.calls)
        self.assertTrue(draft.tool_events)
        self.assertTrue(confirmed.tool_events)


if __name__ == "__main__":
    unittest.main()
