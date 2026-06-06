from __future__ import annotations

from activity_agent.domain.models import AfterActionReview, PlanOption


class ReviewMemory:
    """Builds after-action reviews and lightweight preference memory."""

    def create_review(
        self,
        option: PlanOption,
        actual_cost_per_person: int,
        attendance: int,
        ratings: dict[str, float],
        complaints: list[str] | None = None,
    ) -> AfterActionReview:
        complaints = complaints or []
        best_segment = self._best_segment(option, ratings)
        updated_preferences = self._updated_preferences(best_segment, ratings, complaints)
        next_recommendations = self._next_recommendations(option, updated_preferences)
        share_copy = (
            f"这次“{option.theme_name}”完成啦：实际人均 {actual_cost_per_person} 元，"
            f"最受欢迎的是 {best_segment}。下次可以试试 {next_recommendations[0]}。"
        )
        return AfterActionReview(
            actual_cost_per_person=actual_cost_per_person,
            attendance=attendance,
            ratings=ratings,
            best_segment=best_segment,
            complaints=complaints,
            updated_preferences=updated_preferences,
            next_recommendations=next_recommendations,
            share_copy=share_copy,
        )

    def _best_segment(self, option: PlanOption, ratings: dict[str, float]) -> str:
        if ratings:
            best_key = max(ratings.items(), key=lambda pair: pair[1])[0]
            for item in option.timeline_items:
                if item.merchant_id == best_key or item.merchant_name == best_key:
                    return item.merchant_name
        return max(option.timeline_items, key=lambda item: item.price_estimate).merchant_name

    def _updated_preferences(self, best_segment: str, ratings: dict[str, float], complaints: list[str]) -> list[str]:
        preferences = [f"偏好更新：对“{best_segment}”反馈最好。"]
        if any(score < 3.5 for score in ratings.values()):
            preferences.append("下次降低低分环节的时长或替换同类型供给。")
        if complaints:
            preferences.append("下次提前规避：" + "、".join(complaints))
        return preferences

    def _next_recommendations(self, option: PlanOption, preferences: list[str]) -> list[str]:
        if "回血" in option.theme_name:
            return ["轻徒步 + 咖啡 + 温泉", "拳击体验 + 烤肉 + KTV", "展览 + 小酒馆 + 夜景散步"]
        if "纪念日" in option.theme_name or "约会" in option.theme_name:
            return ["双人烘焙 + 花园餐厅 + 江边散步", "香薰手作 + 甜品 + 小花束", "泡汤酒店 + 双人早餐"]
        return ["城市影像展 + 咖啡甜品 + 夜景散步", "开放麦 + 夜市 + 自助 KTV", "桌游 + 火锅 + 推拿"]
