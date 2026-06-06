from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime

from activity_agent.domain.models import RouteResult, Scene, UserRequest


MOOD_DICTIONARY: list[tuple[str, list[str]]] = [
    ("回血", ["回血"]),
    ("班味", ["回血"]),
    ("累", ["回血", "养生"]),
    ("无聊", ["新鲜", "聊天"]),
    ("发疯", ["发疯", "解压"]),
    ("解压", ["发疯", "解压"]),
    ("出片", ["出片"]),
    ("拍照", ["出片"]),
    ("聊天", ["聊天", "低耗社交"]),
    ("省钱", ["省钱"]),
    ("便宜", ["省钱"]),
    ("养生", ["养生"]),
    ("微醺", ["微醺"]),
    ("热闹", ["热闹"]),
    ("新鲜", ["新鲜"]),
]

EXPERIENCE_DICTIONARY: list[tuple[str, list[str]]] = [
    ("杭州", ["杭州"]),
    ("杭城", ["杭州"]),
    ("老城", ["杭州", "老城烟火", "本土底蕴"]),
    ("烟火", ["老城烟火", "特色美食"]),
    ("河坊街", ["杭州", "老城烟火", "特色美食"]),
    ("南宋御街", ["杭州", "老城烟火", "本土底蕴"]),
    ("运河", ["杭州", "运河", "人文"]),
    ("桥西", ["杭州", "运河", "人文"]),
    ("西湖", ["杭州", "西湖", "出片"]),
    ("湖滨", ["杭州", "西湖", "低体力"]),
    ("近郊", ["杭州", "近郊山水"]),
    ("山水", ["近郊山水"]),
    ("茶山", ["杭州", "近郊山水", "茶山"]),
    ("龙坞", ["杭州", "近郊山水", "茶山"]),
    ("西溪", ["杭州", "近郊山水", "低体力"]),
    ("湘湖", ["杭州", "近郊山水", "湘湖", "低体力"]),
    ("良渚", ["杭州", "良渚", "本土底蕴", "雨天室内"]),
    ("特色美食", ["杭州", "特色美食"]),
    ("小吃", ["特色美食", "老城烟火"]),
    ("打卡", ["出片"]),
    ("少走路", ["低体力"]),
    ("不想太累", ["低体力"]),
    ("出门", ["低费脑"]),
    ("不想查攻略", ["低费脑", "不想查攻略"]),
    ("不想费脑", ["低费脑", "不想查攻略"]),
    ("没目标", ["低费脑"]),
    ("不知道去哪", ["低费脑"]),
    ("宅家", ["低费脑"]),
    ("下雨", ["雨天室内"]),
    ("雨天", ["雨天室内"]),
]

RELATIONSHIP_STAGE_DICTIONARY: list[tuple[str, str]] = [
    ("约TA", "暧昧/追求中"),
    ("约ta", "暧昧/追求中"),
    ("暧昧", "暧昧/追求中"),
    ("追求", "暧昧/追求中"),
    ("第一次", "暧昧/追求中"),
    ("刚在一起", "刚在一起"),
    ("稳定", "稳定情侣"),
    ("女朋友", "稳定情侣"),
    ("男朋友", "稳定情侣"),
    ("对象", "稳定情侣"),
    ("纪念日", "纪念日"),
    ("修复", "想修复关系"),
    ("吵架", "想修复关系"),
    ("惊喜", "想制造惊喜"),
]

RELATIONSHIP_GOAL_DICTIONARY: list[tuple[str, str]] = [
    ("约出来", "降低邀约门槛"),
    ("怕尴尬", "降低尴尬"),
    ("升温", "自然升温"),
    ("浪漫", "增加浪漫感"),
    ("纪念日", "制造仪式感"),
    ("修复", "缓和关系"),
    ("道歉", "缓和关系"),
    ("过夜", "夜宿闭环"),
    ("酒店", "夜宿闭环"),
    ("礼物", "送礼表达"),
    ("惊喜", "制造惊喜"),
]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _parse_budget(text: str) -> int | None:
    explicit = re.search(r'(?:人均|预算|每人|控制在|控在)\D{0,6}(\d{2,4})', text)
    if explicit:
        return int(explicit.group(1))
    loose = re.search(r'(\d{2,4})\s*(?:元|块|rmb|RMB)', text)
    return int(loose.group(1)) if loose else None


def _parse_party_size(text: str, scene: Scene) -> int | None:
    range_match = re.search(r'(\d+)\s*[-~到至]\s*(\d+)\s*(?:个人|人)', text)
    if range_match:
        return int(range_match.group(2))
    explicit = re.search(r'(\d+)\s*(?:个人|人)', text)
    if explicit:
        return int(explicit.group(1))
    return 2 if scene == Scene.COUPLE else None


def _parse_time_window(text: str, scene: Scene) -> str | None:
    """
    时间窗口解析 - 使用本地真实时间
    
    根据当前时间和用户输入智能推断合适的时间窗口
    """
    now = datetime.now()
    current_hour = now.hour

    if "今晚" in text or "今天晚上" in text:
        if current_hour < 17:
            return "today 18:30-23:30"
        elif current_hour < 20:
            return f"today {current_hour+1}:00-23:30"
        else:
            return "today 20:00-23:00"
    elif "明晚" in text or "明天晚上" in text:
        return "tomorrow 18:30-23:30"
    elif "周五" in text:
        return "friday 18:30-23:30"
    elif "周末" in text:
        return "weekend 15:00-23:30" if scene == Scene.COUPLE else "weekend 14:00-22:30"
    elif "下午" in text:
        return "selected_day 15:00-20:30"
    elif "晚上" in text:
        return "selected_day 18:30-23:30"
    return None


def _parse_location(text: str) -> str | None:
    if "杭州" in text or "杭城" in text or any(word in text for word in ["西湖", "河坊街", "南宋御街", "运河", "桥西", "龙坞", "西溪", "湘湖", "良渚"]):
        return "hangzhou"
    match = re.search(r'(?:在|从|离|附近|靠近)([\u4e00-\u9fa5A-Za-z0-9]{2,12})(?:附近|出发|周边|这边)?', text)
    if match:
        return match.group(1)
    if "别太远" in text or "附近" in text:
        return "current_location"
    return None


def _parse_mood_tags(text: str) -> list[str]:
    tags: list[str] = []
    for keyword, values in MOOD_DICTIONARY:
        if keyword in text:
            tags.extend(values)
    return _unique(tags)


def _parse_experience_tags(text: str) -> list[str]:
    tags: list[str] = []
    for keyword, values in EXPERIENCE_DICTIONARY:
        if keyword in text:
            tags.extend(values)
    return _unique(tags)


def _parse_journey_duration(text: str) -> str | None:
    if any(word in text for word in ["整天", "整日", "一天", "一日", "周末"]):
        return "full_day"
    if any(word in text for word in ["半天", "半日", "下午", "晚上", "今晚"]):
        return "half_day"
    return None


def _first_match(text: str, dictionary: list[tuple[str, str]]) -> str | None:
    return next((value for keyword, value in dictionary if keyword in text), None)


def _parse_hard_constraints(text: str) -> dict[str, bool]:
    return {
        "no_alcohol": "不喝酒" in text or "不要酒" in text,
        "indoor_only": "室内" in text or "下雨" in text,
        "cheaper": "便宜" in text or "省钱" in text or "预算太高" in text,
        "photo_friendly": "出片" in text or "拍照" in text,
        "quiet": "安静" in text or "不吵" in text,
        "hotel_wanted": "酒店" in text or "过夜" in text or "夜宿" in text or "民宿" in text,
        "gift_wanted": "礼物" in text or "花" in text or "蛋糕" in text or "惊喜" in text,
        "partial_allowed": "只参加" in text or "后半场" in text,
    }


class ContextCollector:
    """Extracts a minimally sufficient UserRequest from natural language."""

    def collect(
        self,
        route: RouteResult,
        text: str,
        partial_request: UserRequest | None = None,
    ) -> tuple[UserRequest, list[str], list[str]]:
        normalized = str(text or "")
        scene = partial_request.scene if partial_request else route.scene
        parsed_budget = _parse_budget(normalized)
        constraints = _parse_hard_constraints(normalized)

        if partial_request:
            constraints = {**partial_request.hard_constraints, **constraints}

        parsed_experience_tags = _parse_experience_tags(normalized)
        is_city_day_out = bool(parsed_experience_tags)
        default_budget = 360 if scene == Scene.COUPLE else 220
        if constraints["cheaper"] and parsed_budget is None and not partial_request:
            default_budget = 260 if scene == Scene.COUPLE else 150

        request = UserRequest(
            scene=scene,
            time_window=(partial_request.time_window if partial_request else None)
            or _parse_time_window(normalized, scene)
            or ("weekend 15:00-22:30" if scene == Scene.COUPLE else "today 18:30-23:30"),
            location_anchor=(partial_request.location_anchor if partial_request else None)
            or _parse_location(normalized)
            or "current_location",
            budget_per_person=(partial_request.budget_per_person if partial_request else None)
            or parsed_budget
            or default_budget,
            party_size=(partial_request.party_size if partial_request else None)
            or _parse_party_size(normalized, scene)
            or (2 if scene == Scene.COUPLE else 4),
            mood_tags=_unique([*(partial_request.mood_tags if partial_request else []), *_parse_mood_tags(normalized)]),
            relationship_stage=(partial_request.relationship_stage if partial_request else None)
            or ("稳定情侣" if scene == Scene.COUPLE else None),
            relationship_goal=(partial_request.relationship_goal if partial_request else None)
            or ("创造共同体验" if scene == Scene.COUPLE else None),
            hard_constraints=constraints,
            journey_duration=(partial_request.journey_duration if partial_request else None)
            or _parse_journey_duration(normalized)
            or ("half_day" if is_city_day_out else "evening"),
            experience_tags=_unique([*(partial_request.experience_tags if partial_request else []), *parsed_experience_tags]),
            planning_effort=(
                "zero_effort"
                if any(word in normalized for word in ["不想查攻略", "不想费脑", "没目标", "不知道去哪", "直接安排"])
                else ((partial_request.planning_effort if partial_request else None) or "guided")
            ),
            travel_radius_km=(
                partial_request.travel_radius_km
                if partial_request
                else (12.0 if any(tag in parsed_experience_tags for tag in ["近郊山水", "茶山", "良渚"]) else 4.0)
            ),
            weather_sensitive=("下雨" in normalized or "雨天" in normalized or constraints["indoor_only"]),
        )

        if scene == Scene.COUPLE:
            request = replace(
                request,
                relationship_stage=_first_match(normalized, RELATIONSHIP_STAGE_DICTIONARY) or request.relationship_stage,
                relationship_goal=_first_match(normalized, RELATIONSHIP_GOAL_DICTIONARY) or request.relationship_goal,
            )

        if scene == Scene.FRIENDS and not request.mood_tags:
            request = replace(request, mood_tags=["新鲜", "低耗社交"])
        if scene == Scene.COUPLE and not request.mood_tags:
            fallback_moods = ["轻互动", "安全"] if request.relationship_stage == "暧昧/追求中" else ["浪漫", "保鲜"]
            request = replace(request, mood_tags=fallback_moods)

        return request, self._missing_questions(request), self._assumptions(request, normalized, parsed_budget)

    def _missing_questions(self, request: UserRequest) -> list[str]:
        if request.scene == Scene.FRIENDS:
            return [
                question
                for question in [
                    None if request.party_size else "大概几个人？",
                    None if request.time_window else "大概什么时候出发？",
                    None if request.budget_per_person else "人均预算大概多少？",
                    None if request.mood_tags else "今晚想要回血、发疯、出片、聊天还是省钱？",
                ]
                if question
            ]

        return [
            question
            for question in [
                None if request.relationship_stage else "这是暧昧/追求中、刚在一起、稳定情侣，还是纪念日？",
                None if request.relationship_goal else "这次更想升温、浪漫、修复、过夜，还是送礼？",
                None if request.time_window else "希望安排在什么时间？",
                None if request.budget_per_person else "人均预算大概多少？",
            ]
            if question
        ]

    def _assumptions(self, request: UserRequest, text: str, parsed_budget: int | None) -> list[str]:
        assumptions: list[str] = []
        if parsed_budget is None and "预算" not in text:
            assumptions.append(f"未给预算，先按人均 {request.budget_per_person} 元生成。")
        if "人" not in text and request.scene == Scene.FRIENDS:
            assumptions.append(f"未给人数，先按 {request.party_size} 人朋友局估算。")
        if request.location_anchor == "current_location":
            assumptions.append("未给具体商圈，先按当前位置 3km 内优先。")
        if request.location_anchor == "hangzhou":
            assumptions.append("已按杭州本地主题局生成，外部地图/天气/库存为 seed 估算。")
        if request.planning_effort == "zero_effort":
            assumptions.append("已按低费脑模式处理，优先给可直接照着走的完整路线。")
        if request.scene == Scene.COUPLE and not _first_match(text, RELATIONSHIP_STAGE_DICTIONARY):
            assumptions.append(f"未给关系阶段，先按{request.relationship_stage}处理。")
        return assumptions
