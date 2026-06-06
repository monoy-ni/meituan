from __future__ import annotations

from activity_agent.domain.models import Intent, RouteResult, Scene


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


class IntentRouter:
    """Routes raw user utterances into an Agent intent and scene."""

    def route(self, text: str, scene_hint: Scene | None = None) -> RouteResult:
        normalized = str(text or "").strip()
        signals: list[str] = []

        intent = Intent.PLAN
        if _contains_any(normalized, ["复盘", "评分", "结束了", "实际人均", "最喜欢", "下次推荐"]):
            intent = Intent.REVIEW
            signals.append("review_keyword")
        elif _contains_any(normalized, ["确认预约", "下单", "订票", "预约", "支付", "发起aa", "发起AA", "买单"]):
            intent = Intent.BOOKING
            signals.append("booking_keyword")
        elif _contains_any(normalized, ["预算太高", "晚点到", "不喝酒", "只参加", "有人", "反馈", "去不了"]):
            intent = Intent.FEEDBACK
            signals.append("feedback_keyword")
        elif _contains_any(normalized, ["换", "便宜点", "室内", "不要", "更适合", "改成"]):
            intent = Intent.ADJUST
            signals.append("adjust_keyword")

        scene = scene_hint
        if scene is None and _contains_any(
            normalized,
            ["情侣", "女朋友", "男朋友", "对象", "约会", "暧昧", "追求", "纪念日", "TA", "ta", "修复关系", "表白"],
        ):
            scene = Scene.COUPLE
            signals.append("couple_keyword")
        if scene is None and _contains_any(normalized, ["朋友", "组局", "同事", "群", "几个人", "哥们", "姐妹", "局"]):
            scene = Scene.FRIENDS
            signals.append("friends_keyword")
        if scene is None:
            scene = Scene.FRIENDS
            signals.append("default_friends_scene")

        confidence = 0.86 if len(signals) >= 2 else 0.68
        return RouteResult(intent=intent, scene=scene, confidence=confidence, signals=signals)

