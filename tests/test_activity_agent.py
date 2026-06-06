import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import FeedbackStatus, InviteFeedback, PayMode, Scene, TimelineType


class ActivityPlanningAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ActivityPlanningAgent()

    def test_sparse_friends_request_generates_three_theme_options(self) -> None:
        result = self.agent.plan("今晚有点无聊，想叫朋友出来")

        self.assertEqual(result.request.scene, Scene.FRIENDS)
        self.assertEqual(len(result.options), 3)
        self.assertTrue(all(option.timeline_items for option in result.options))

        card = self.agent.render_share_card(result.options[0], result.request)
        self.assertIn("【", card)
        self.assertIn("[我想去]", card)
        self.assertIn("一键预约", card)

    def test_feedback_resolves_budget_late_arrival_and_no_alcohol(self) -> None:
        result = self.agent.plan("周五下班后想找朋友玩，预算人均220，4个人，想回血")
        option = result.options[0]
        feedback = [
            InviteFeedback("小王", FeedbackStatus.JOIN, budget_feedback=180, preference_tags=["聊天"]),
            InviteFeedback("小李", FeedbackStatus.LATE, time_feedback="20:30后到"),
            InviteFeedback("小陈", FeedbackStatus.JOIN, dietary_or_boundary_constraints=["不喝酒"]),
            InviteFeedback("小周", FeedbackStatus.PARTIAL, preference_tags=["省钱"]),
        ]

        revised_request, revised_option, notes = self.agent.resolve_feedback(result.request, feedback, option.theme_name)

        self.assertLessEqual(revised_request.budget_per_person, 180)
        self.assertTrue(revised_request.hard_constraints["no_alcohol"])
        self.assertTrue(revised_request.hard_constraints["partial_allowed"])
        self.assertLessEqual(revised_option.estimated_cost_per_person, revised_request.budget_per_person)
        self.assertTrue(any("晚到" in note for note in notes))

    def test_adjust_request_can_make_plan_cheaper_and_no_alcohol(self) -> None:
        initial = self.agent.plan("今晚下班回血局，预算人均240，4个人")
        adjusted = self.agent.plan("A 但便宜点，不喝酒", partial_request=initial.request)

        self.assertLess(adjusted.request.budget_per_person, initial.request.budget_per_person)
        self.assertTrue(adjusted.request.hard_constraints["no_alcohol"])
        self.assertEqual(len(adjusted.options), 3)

    def test_couple_pursuit_outputs_low_pressure_date(self) -> None:
        result = self.agent.plan("想约TA出来，怕尴尬，周末下午，人均300")
        option = result.options[0]

        self.assertEqual(result.request.scene, Scene.COUPLE)
        self.assertEqual(result.request.relationship_stage, "暧昧/追求中")
        self.assertEqual(option.theme_name, "轻升温不尴尬约会")
        self.assertFalse(any(item.type == TimelineType.HOTEL for item in option.timeline_items))
        self.assertIn("要不要一起去试试", option.invite_copy)

    def test_booking_draft_requires_confirmation_before_payment(self) -> None:
        result = self.agent.plan("纪念日想安排酒店和花，预算人均700")
        option = result.options[0]
        draft = self.agent.create_booking_draft(option, result.request, PayMode.SINGLE_PAY)

        self.assertTrue(draft.confirmation_required)
        self.assertEqual(draft.pay_mode, PayMode.SINGLE_PAY)
        self.assertIn("不会未经授权支付", draft.safety_notice)
        self.assertTrue(any(item.type == TimelineType.HOTEL for item in draft.items))

    def test_after_action_review_generates_memory_and_next_recommendations(self) -> None:
        result = self.agent.plan("今晚想组个下班回血局，预算人均220，4个人")
        option = result.options[0]
        review = self.agent.create_review(
            option,
            actual_cost_per_person=206,
            attendance=4,
            ratings={option.timeline_items[1].merchant_name: 4.8},
        )

        self.assertEqual(review.actual_cost_per_person, 206)
        self.assertEqual(review.attendance, 4)
        self.assertIn(option.timeline_items[1].merchant_name, review.best_segment)
        self.assertTrue(review.next_recommendations)
        self.assertIn("完成啦", review.share_copy)


if __name__ == "__main__":
    unittest.main()

