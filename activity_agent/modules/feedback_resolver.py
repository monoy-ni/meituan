from __future__ import annotations

from dataclasses import replace

from activity_agent.domain.models import FeedbackStatus, InviteFeedback, PlanOption, UserRequest
from activity_agent.modules.itinerary_composer import ItineraryComposer
from activity_agent.modules.theme_planner import ThemePlanner


class FeedbackResolver:
    """Converts invite feedback into a tighter request and a revised plan."""

    def __init__(self, theme_planner: ThemePlanner | None = None, composer: ItineraryComposer | None = None) -> None:
        self.theme_planner = theme_planner or ThemePlanner()
        self.composer = composer or ItineraryComposer()

    def resolve(
        self,
        request: UserRequest,
        feedback: list[InviteFeedback],
        preferred_theme_name: str | None = None,
    ) -> tuple[UserRequest, PlanOption, list[str]]:
        constraints = dict(request.hard_constraints)
        notes: list[str] = []
        joined_or_late = [item for item in feedback if item.status in {FeedbackStatus.JOIN, FeedbackStatus.LATE, FeedbackStatus.PARTIAL}]
        budget_values = [item.budget_feedback for item in feedback if item.budget_feedback]

        if budget_values:
            new_budget = min(request.budget_per_person, min(budget_values))
            if new_budget < request.budget_per_person:
                notes.append(f"已按最低可接受预算收敛到人均 {new_budget} 元。")
        else:
            new_budget = request.budget_per_person

        preference_tags: list[str] = []
        for item in feedback:
            preference_tags.extend(item.preference_tags)
            joined_constraints = " ".join(item.dietary_or_boundary_constraints)
            if "不喝酒" in joined_constraints:
                constraints["no_alcohol"] = True
                notes.append("已过滤微醺/酒吧供给。")
            if "室内" in joined_constraints:
                constraints["indoor_only"] = True
                notes.append("已优先室内供给。")
            if item.status == FeedbackStatus.LATE:
                constraints["partial_allowed"] = True
                notes.append(f"{item.participant_id} 会晚到，保留后半场可加入的安排。")
            if item.status == FeedbackStatus.PARTIAL:
                constraints["partial_allowed"] = True
                notes.append(f"{item.participant_id} 只参加部分行程，卡片保留局部参与入口。")

        revised_request = replace(
            request,
            budget_per_person=new_budget,
            party_size=max(1, len(joined_or_late) or request.party_size),
            mood_tags=list(dict.fromkeys([*request.mood_tags, *preference_tags])),
            hard_constraints=constraints,
        )

        themes = self.theme_planner.plan(revised_request)
        if preferred_theme_name:
            themes = sorted(themes, key=lambda theme: theme.name != preferred_theme_name)
        options = self.composer.compose(themes, revised_request)
        best = min(options, key=lambda option: max(0, option.estimated_cost_per_person - revised_request.budget_per_person))
        notes.append(f"已保留“{best.theme_name}”方向并生成可执行版本。")
        return revised_request, best, list(dict.fromkeys(notes))

    def cheaper_version(self, request: UserRequest, preferred_theme_name: str | None = None) -> tuple[UserRequest, PlanOption]:
        revised = replace(
            request,
            budget_per_person=max(80, int(request.budget_per_person * 0.75)),
            mood_tags=list(dict.fromkeys([*request.mood_tags, "省钱"])),
            hard_constraints={**request.hard_constraints, "cheaper": True},
        )
        themes = self.theme_planner.plan(revised)
        if preferred_theme_name:
            themes = sorted(themes, key=lambda theme: theme.name != preferred_theme_name)
        return revised, self.composer.compose(themes, revised)[0]

