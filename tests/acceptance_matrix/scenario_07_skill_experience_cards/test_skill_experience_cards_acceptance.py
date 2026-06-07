import unittest

from activity_agent import ActivityPlanningAgent


REQUIRED_CARD_KEYS = {
    "designer",
    "title",
    "theme_line",
    "vibe_tags",
    "play_style",
    "flow",
    "signature_moments",
    "host_tips",
    "booking_note",
}


class SkillExperienceCardsAcceptanceTest(unittest.TestCase):
    def test_friends_use_themed_outing_designer_card(self) -> None:
        result = ActivityPlanningAgent().plan("朋友局，今晚下班回血，4个人，人均220")
        option = result.options[0]
        card = option.experience_card

        self.assertEqual(card["designer"], "themed-outing-designer")
        self.assertTrue(REQUIRED_CARD_KEYS <= set(card))
        self.assertTrue(card["flow"])
        self.assertEqual(len(card["flow"]), len(option.timeline_items))
        self.assertIn("确认前不会", card["booking_note"])

    def test_couple_use_couple_date_designer_card(self) -> None:
        result = ActivityPlanningAgent().plan("想约TA出来，怕尴尬，周末下午，人均300")
        option = result.options[0]
        card = option.experience_card

        self.assertEqual(card["designer"], "couple-date-designer")
        self.assertTrue(REQUIRED_CARD_KEYS <= set(card))
        self.assertTrue(card["flow"])
        self.assertEqual(len(card["flow"]), len(option.timeline_items))
        self.assertIn("确认前不会", card["booking_note"])


if __name__ == "__main__":
    unittest.main()
