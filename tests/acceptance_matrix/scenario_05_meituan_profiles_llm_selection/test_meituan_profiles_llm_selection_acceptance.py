import json
import unittest
from dataclasses import replace

from activity_agent.domain.models import MerchantSupply, Scene, Theme, ThemeSlot, TimelineType, UserRequest
from activity_agent.llm.itinerary_curator import LLMItineraryCurator
from activity_agent.modules.itinerary_composer import ItineraryComposer
from activity_agent.modules.supply_matcher import SupplyMatcher
from activity_agent.tools.mock_meituan import MockMeituanToolClient


class FakeCuratorLLM:
    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []

    def complete(self, messages):
        self.messages.append(messages)
        return json.dumps(
            {"merchant_ids": ["food_bbq", "activity_ktv", "relax_tea", "made_up_merchant"]},
            ensure_ascii=False,
        )


def _supply(merchant_id: str, name: str, item_type: TimelineType, tags: list[str], price: int) -> MerchantSupply:
    return MerchantSupply(
        id=merchant_id,
        name=name,
        type=item_type,
        price=price,
        duration_minutes=60,
        distance_km=1.0,
        district="萧山区",
        tags=tags,
        scene_fit=[Scene.FRIENDS],
        booking_modes=["reservation"],
        available=True,
        why=f"{name} 适合主题局。",
        address="奥映世纪轩周边",
        latitude=30.243,
        longitude=120.243,
        area_cluster="xianghu_lake",
        data_confidence="mock",
        matched_keywords=tags[:1],
    )


class MeituanProfilesLLMSelectionAcceptanceTest(unittest.TestCase):
    def test_mock_profiles_enter_llm_and_drive_theme_combination(self) -> None:
        catalog = [
            _supply("food_bbq", "热闹烧烤店", TimelineType.DINING, ["烧烤", "回血"], 98),
            _supply("activity_ktv", "下班K歌房", TimelineType.ACTIVITY, ["KTV", "解压"], 88),
            _supply("relax_tea", "收尾茶馆", TimelineType.RELAX, ["茶馆", "聊天"], 68),
        ]
        meituan = MockMeituanToolClient(catalog)
        profiled_catalog = [
            replace(supply, merchant_profile=dict(meituan.merchant_profile(supply.id, supply.name).data))
            for supply in catalog
        ]
        theme = Theme(
            id="acceptance_recovery",
            name="下班回血主题局",
            emotional_hook="先释放，再吃热的，最后收住聊天。",
            slots=[
                ThemeSlot(TimelineType.ACTIVITY, ["KTV", "解压"], "先释放压力"),
                ThemeSlot(TimelineType.DINING, ["烧烤", "回血"], "吃一口热的"),
                ThemeSlot(TimelineType.RELAX, ["茶馆", "聊天"], "低压力收尾"),
            ],
            add_ons=[],
        )
        request = UserRequest(
            scene=Scene.FRIENDS,
            time_window="today 18:30-23:30",
            location_anchor="奥映世纪轩",
            budget_per_person=260,
            party_size=4,
            mood_tags=["回血", "解压"],
        )
        llm = FakeCuratorLLM()

        preferred_ids = LLMItineraryCurator(llm).preferred_supply_ids(theme, request, profiled_catalog)
        request = replace(request, hard_constraints={"preferred_supply_ids": preferred_ids})
        option = ItineraryComposer(SupplyMatcher(profiled_catalog)).compose([theme], request)[0]

        prompt = llm.messages[0][1]["content"]
        selected_ids = [item.merchant_id for item in option.timeline_items]

        self.assertEqual(preferred_ids, ["food_bbq", "activity_ktv", "relax_tea"])
        self.assertNotIn("made_up_merchant", preferred_ids)
        self.assertIn("mock 用户评价摘要", prompt)
        self.assertIn("mock 商户介绍", prompt)
        self.assertEqual(set(selected_ids), set(preferred_ids))
        self.assertEqual({item.type for item in option.timeline_items}, {TimelineType.ACTIVITY, TimelineType.DINING, TimelineType.RELAX})


if __name__ == "__main__":
    unittest.main()
