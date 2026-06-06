from __future__ import annotations

from activity_agent.domain.models import PlanOption, Scene, UserRequest


class ShareCardGenerator:
    """Renders PlanOption objects as shareable cards for chat or private invites."""

    def render(self, option: PlanOption, request: UserRequest) -> str:
        lines = [
            f"【{option.theme_name}】",
            "",
            option.emotional_hook,
            "",
        ]
        for item in option.timeline_items:
            lines.append(
                f"{item.start_time}-{item.end_time}  {item.merchant_name}｜{item.why_this_fits.split('：', 1)[0]}"
            )

        lines.extend(
            [
                "",
                f"适合：{self._fit_text(request)}",
                f"人均：约 {option.estimated_cost_per_person} 元",
                f"距离：全程约 {option.total_distance}km",
                f"预约状态：{option.booking_readiness.value}",
                "可替换：" + " / ".join(option.replaceable_slots),
            ]
        )

        if option.risk_notes:
            lines.append("注意：" + "；".join(option.risk_notes))

        lines.append("")
        lines.append("[" + "] [".join(option.actions) + "]")

        if request.scene == Scene.COUPLE and option.invite_copy:
            lines.extend(["", "邀约话术：", option.invite_copy])
        if option.dating_tips:
            lines.extend(["", "贴心提醒：", *[f"- {tip}" for tip in option.dating_tips]])

        return "\n".join(lines)

    def _fit_text(self, request: UserRequest) -> str:
        if request.scene == Scene.FRIENDS:
            return "想见朋友但不想费脑、需要一个能发出去的出门理由的人"
        if request.relationship_stage == "暧昧/追求中":
            return "想自然约出来、降低尴尬和拒绝压力的人"
        return "想给关系增加共同体验、仪式感和轻松陪伴的人"
