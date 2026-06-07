from __future__ import annotations

import json
from typing import Any

from activity_agent.domain.models import PlanOption, Scene, TimelineItem, TimelineType, UserRequest
from activity_agent.llm import LLMClient


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


FRIEND_THEME_PROFILES: dict[str, dict[str, object]] = {
    "下班回血局": {
        "tags": ["回血", "夜宵", "低负担"],
        "line": "把下班后的低电量先接住，再用热闹和夜宵慢慢充回来。",
        "style": "先卸掉班味，再吃一口热的，最后用一个可进可退的收尾点把聊天留住。",
    },
    "多巴胺补给局": {
        "tags": ["多巴胺", "热闹", "能量补给"],
        "line": "用颜色、声音和热乎食物把今天从灰色拉回高饱和。",
        "style": "每一站都安排一个即时反馈，让大家不用酝酿也能进入状态。",
    },
    "出片局": {
        "tags": ["出片", "城市感", "轻社交"],
        "line": "把路线设计成一组能发出去的城市切片。",
        "style": "先找画面，再找食物，最后用一个不赶路的点收照片和聊天。",
    },
    "松弛聊天局": {
        "tags": ["松弛", "聊天", "慢节奏"],
        "line": "不赶场、不硬嗨，只给朋友留一段能说真话的时间。",
        "style": "降低噪音和决策成本，把每站都做成自然接话的缓冲区。",
    },
    "破冰社交局": {
        "tags": ["破冰", "轻互动", "低压力"],
        "line": "先让人有事可做，再让话自然发生。",
        "style": "用规则感活动开场，用共同食物接住陌生感，用收尾任务留下下一次理由。",
    },
    "低成本快乐局": {
        "tags": ["低成本", "快乐", "AA友好"],
        "line": "钱少一点，笑点和参与感不能少。",
        "style": "把预算花在最有记忆点的一站，其余用轻量玩法串起来。",
    },
    "城市副本局": {
        "tags": ["副本", "探索", "通关"],
        "line": "把普通城市路线包装成一晚上的小副本。",
        "style": "每一站都是一个关卡，拍照、吃饭和收尾都变成通关奖励。",
    },
    "发疯解压局": {
        "tags": ["解压", "发疯", "释放"],
        "line": "把压力先甩出去，再把快乐补回来。",
        "style": "先高释放，再高热量补给，最后用夜间场景延长情绪峰值。",
    },
    "早睡养生局": {
        "tags": ["养生", "早收", "舒服"],
        "line": "认真见朋友，也认真放过明天的自己。",
        "style": "安排舒服、可提前结束的动线，保留获得感但不拖到深夜。",
    },
    "友情充电局": {
        "tags": ["友情", "充电", "老朋友"],
        "line": "不是凑一顿饭，是给关系续一点电。",
        "style": "用熟悉感开场，用共同体验制造新话题，用收尾仪式把这次见面留下来。",
    },
}


COUPLE_STAGE_PROFILES: dict[str, dict[str, object]] = {
    "初识/暧昧": {
        "purpose": "不尴尬破冰，降低压力，增加自然互动",
        "tags": ["低压力", "自然互动", "安全感"],
        "line": "让两个人先舒服地待在同一个节奏里，不急着确认关系。",
    },
    "追求期": {
        "purpose": "轻升温约会，创造好感和安全感",
        "tags": ["轻升温", "好感", "安全感"],
        "line": "把好感藏在顺手的照顾和不压迫的互动里。",
    },
    "刚在一起": {
        "purpose": "第一次认真约会，建立仪式感",
        "tags": ["认真约会", "仪式感", "共同记忆"],
        "line": "让第一次正式约会有一点被记住的形状。",
    },
    "稳定期": {
        "purpose": "日常保鲜约会，打破重复感",
        "tags": ["保鲜", "日常换气", "共同体验"],
        "line": "不靠大阵仗，用新的共同体验把日常重新点亮。",
    },
    "纪念日": {
        "purpose": "高仪式感约会，强化关系记忆",
        "tags": ["纪念日", "仪式感", "关系记忆"],
        "line": "把这一天从日历里单独拎出来，变成你们能复述的记忆。",
    },
    "吵架后": {
        "purpose": "修复型约会，弱化冲突，创造缓和空间",
        "tags": ["修复", "缓和", "低刺激"],
        "line": "先把气氛放软，再给话题一个不对抗的入口。",
    },
    "异地见面": {
        "purpose": "高密度陪伴约会，最大化共同体验",
        "tags": ["高密度陪伴", "久别重逢", "共同体验"],
        "line": "把有限的见面时间变成连续、饱满、不浪费的陪伴。",
    },
    "夜宿需求": {
        "purpose": "酒店/民宿收尾约会，延展私密空间",
        "tags": ["夜宿", "私密收尾", "确认边界"],
        "line": "把夜宿放在双方都确认后的柔软收尾里，而不是路线压力里。",
    },
}


class ExperienceCardDesigner:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.friend_designer = ThemedOutingDesigner(llm_client)
        self.couple_designer = CoupleDateDesigner(llm_client)

    def design(self, option: PlanOption, request: UserRequest) -> dict[str, Any]:
        if request.scene == Scene.COUPLE:
            return self.couple_designer.design(option, request)
        return self.friend_designer.design(option, request)


class ThemedOutingDesigner:
    designer_name = "themed-outing-designer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def design(self, option: PlanOption, request: UserRequest) -> dict[str, Any]:
        return _llm_card(self.llm_client, self.designer_name, _friend_prompt(option, request), option) or self._fallback(option, request)

    def _fallback(self, option: PlanOption, request: UserRequest) -> dict[str, Any]:
        profile = _friend_profile(option.theme_name, request.mood_tags)
        tags = list(profile["tags"])[:4]
        location = _area_label(option)
        return {
            "designer": self.designer_name,
            "title": f"{location}{option.theme_name}",
            "theme_line": str(profile["line"]),
            "vibe_tags": tags,
            "play_style": str(profile["style"]),
            "flow": [_friend_flow_item(item, index, profile) for index, item in enumerate(option.timeline_items)],
            "signature_moments": _friend_signature_moments(option, profile),
            "host_tips": _friend_host_tips(option, request),
            "booking_note": "玩法卡已生成；下一步只创建预约草稿，用户确认前不会支付或下不可逆订单。",
        }


class CoupleDateDesigner:
    designer_name = "couple-date-designer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def design(self, option: PlanOption, request: UserRequest) -> dict[str, Any]:
        return _llm_card(self.llm_client, self.designer_name, _couple_prompt(option, request), option) or self._fallback(option, request)

    def _fallback(self, option: PlanOption, request: UserRequest) -> dict[str, Any]:
        stage = _couple_stage_key(option, request)
        profile = COUPLE_STAGE_PROFILES[stage]
        return {
            "designer": self.designer_name,
            "title": f"{stage}｜{option.theme_name}",
            "theme_line": str(profile["line"]),
            "vibe_tags": list(profile["tags"])[:4],
            "play_style": str(profile["purpose"]),
            "flow": [_couple_flow_item(item, index, stage) for index, item in enumerate(option.timeline_items)],
            "signature_moments": _couple_signature_moments(option, stage),
            "host_tips": _couple_host_tips(option, request, stage),
            "booking_note": "玩法卡已生成；预约、酒店、礼物和支付都只会进入待确认草稿，确认前不会执行。",
        }


def _llm_card(llm_client: LLMClient | None, designer: str, prompt: dict[str, Any], option: PlanOption) -> dict[str, Any] | None:
    if llm_client is None:
        return None
    try:
        raw = llm_client.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "你是体验卡 designer。只输出 JSON，不要 markdown。只能引用输入里的 timeline_items，"
                        "不得新增商户，不得承诺已预约/已付款/已下单。"
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ]
        )
        payload = json.loads(raw)
    except Exception:
        return None
    return _validated_card(payload, designer, option)


def _friend_prompt(option: PlanOption, request: UserRequest) -> dict[str, Any]:
    return {
        "designer": "themed-outing-designer",
        "theme_name": option.theme_name,
        "request": _request_payload(request),
        "timeline_items": [_timeline_payload(item) for item in option.timeline_items],
        "route_plan": option.route_plan,
        "required_schema": _schema(),
        "rules": _rules(),
    }


def _couple_prompt(option: PlanOption, request: UserRequest) -> dict[str, Any]:
    return {
        "designer": "couple-date-designer",
        "theme_name": option.theme_name,
        "relationship_stage": request.relationship_stage,
        "relationship_goal": request.relationship_goal,
        "request": _request_payload(request),
        "timeline_items": [_timeline_payload(item) for item in option.timeline_items],
        "route_plan": option.route_plan,
        "required_schema": _schema(),
        "rules": [*_rules(), "暧昧/追求中不得安排酒店或高压表白，吵架后不得设计刺激对抗任务。"],
    }


def _request_payload(request: UserRequest) -> dict[str, Any]:
    return {
        "scene": request.scene.value,
        "time_window": request.time_window,
        "origin_name": request.origin_name,
        "budget_per_person": request.budget_per_person,
        "party_size": request.party_size,
        "mood_tags": request.mood_tags,
        "experience_tags": request.experience_tags,
        "relationship_stage": request.relationship_stage,
        "relationship_goal": request.relationship_goal,
    }


def _timeline_payload(item: TimelineItem) -> dict[str, Any]:
    return {
        "merchant_id": item.merchant_id,
        "merchant_name": item.merchant_name,
        "type": item.type.value,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "address": item.address,
        "matched_keywords": item.matched_keywords,
        "merchant_profile": item.merchant_profile,
    }


def _schema() -> dict[str, Any]:
    return {
        "designer": "string",
        "title": "string",
        "theme_line": "string",
        "vibe_tags": ["string"],
        "play_style": "string",
        "flow": [
            {
                "merchant_id": "must be one existing timeline item id",
                "merchant_name": "must match existing timeline item name",
                "time": "HH:MM-HH:MM",
                "role": "string",
                "experience": "string",
            }
        ],
        "signature_moments": ["string"],
        "host_tips": ["string"],
        "booking_note": "string",
    }


def _rules() -> list[str]:
    return [
        "flow 只能引用 timeline_items 中存在的 merchant_id",
        "不要新增商户、酒店、餐厅或景点",
        "不要说已经预约、已经付款、已经下单",
        "booking_note 必须说明用户确认前不会支付或下不可逆订单",
    ]


def _validated_card(payload: Any, designer: str, option: PlanOption) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or not REQUIRED_CARD_KEYS <= set(payload):
        return None
    if str(payload.get("designer")) != designer:
        return None
    allowed = {item.merchant_id: item for item in option.timeline_items}
    flow = payload.get("flow")
    if not isinstance(flow, list) or not flow:
        return None

    normalized_flow = []
    for flow_item in flow:
        if not isinstance(flow_item, dict):
            return None
        merchant_id = str(flow_item.get("merchant_id") or "")
        if merchant_id not in allowed:
            return None
        timeline_item = allowed[merchant_id]
        normalized_flow.append(
            {
                "merchant_id": merchant_id,
                "merchant_name": timeline_item.merchant_name,
                "time": str(flow_item.get("time") or f"{timeline_item.start_time}-{timeline_item.end_time}"),
                "role": str(flow_item.get("role") or _role_for(timeline_item, 0)),
                "experience": str(flow_item.get("experience") or timeline_item.why_this_fits),
            }
        )

    return {
        "designer": designer,
        "title": str(payload.get("title") or option.theme_name),
        "theme_line": str(payload.get("theme_line") or option.emotional_hook),
        "vibe_tags": _string_list(payload.get("vibe_tags"), limit=5),
        "play_style": str(payload.get("play_style") or option.route_story or option.emotional_hook),
        "flow": normalized_flow,
        "signature_moments": _string_list(payload.get("signature_moments"), limit=5),
        "host_tips": _string_list(payload.get("host_tips"), limit=5),
        "booking_note": _safe_booking_note(str(payload.get("booking_note") or "")),
    }


def _safe_booking_note(value: str) -> str:
    blocked_words = ["已付款", "已支付", "已下单", "已预约成功"]
    if any(word in value for word in blocked_words) or not value:
        return "仅生成待确认草稿；用户确认前不会支付或下不可逆订单。"
    return value


def _string_list(value: Any, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()][:limit]


def _friend_profile(theme_name: str, mood_tags: list[str]) -> dict[str, object]:
    for key, profile in FRIEND_THEME_PROFILES.items():
        if key in theme_name:
            return profile
    if "回血" in mood_tags:
        return FRIEND_THEME_PROFILES["下班回血局"]
    if "省钱" in mood_tags:
        return FRIEND_THEME_PROFILES["低成本快乐局"]
    if "出片" in mood_tags:
        return FRIEND_THEME_PROFILES["出片局"]
    if "发疯" in mood_tags or "解压" in mood_tags:
        return FRIEND_THEME_PROFILES["发疯解压局"]
    return FRIEND_THEME_PROFILES["友情充电局"]


def _friend_flow_item(item: TimelineItem, index: int, profile: dict[str, object]) -> dict[str, str]:
    role = _role_for(item, index)
    return {
        "merchant_id": item.merchant_id,
        "merchant_name": item.merchant_name,
        "time": f"{item.start_time}-{item.end_time}",
        "role": role,
        "experience": f"{role}放在「{item.merchant_name}」：{_experience_text(item)} 这一站负责把{_tag_phrase(profile)}落到真实动作里。",
    }


def _couple_flow_item(item: TimelineItem, index: int, stage: str) -> dict[str, str]:
    roles = {
        "初识/暧昧": ["安全开场", "自然升温", "柔软收尾"],
        "追求期": ["低压邀约", "好感加温", "留白收尾"],
        "刚在一起": ["认真开场", "共同记忆", "仪式收尾"],
        "稳定期": ["日常换气", "新鲜体验", "陪伴收尾"],
        "纪念日": ["仪式开场", "记忆峰值", "纪念收尾"],
        "吵架后": ["情绪降温", "缓和对话", "柔软靠近"],
        "异地见面": ["重逢开场", "密度陪伴", "不浪费收尾"],
        "夜宿需求": ["轻体验开场", "晚餐过渡", "确认后收尾"],
    }
    role = roles.get(stage, roles["稳定期"])[min(index, 2)]
    return {
        "merchant_id": item.merchant_id,
        "merchant_name": item.merchant_name,
        "time": f"{item.start_time}-{item.end_time}",
        "role": role,
        "experience": f"{role}放在「{item.merchant_name}」：{_experience_text(item)} 重点是让节奏服务于「{COUPLE_STAGE_PROFILES[stage]['purpose']}」。",
    }


def _role_for(item: TimelineItem, index: int) -> str:
    if item.type == TimelineType.DINING:
        return "补给站"
    if item.type == TimelineType.NIGHTLIFE:
        return "情绪峰值"
    if item.type == TimelineType.RELAX:
        return "低压收尾"
    if item.type == TimelineType.CHECKIN:
        return "记忆点"
    if item.type == TimelineType.HOTEL:
        return "确认后的夜宿收尾"
    if item.type == TimelineType.GIFT:
        return "轻表达"
    return "开局任务" if index == 0 else "互动关卡"


def _experience_text(item: TimelineItem) -> str:
    return item.why_this_fits.split("：", 1)[-1].strip() or item.transport_hint or "保留一个自然互动的节点。"


def _tag_phrase(profile: dict[str, object]) -> str:
    tags = list(profile.get("tags") or [])
    return "、".join(str(tag) for tag in tags[:2]) or "主题体验"


def _friend_signature_moments(option: PlanOption, profile: dict[str, object]) -> list[str]:
    names = [item.merchant_name for item in option.timeline_items[:3]]
    tags = _tag_phrase(profile)
    return [
        f"开场先给这局定调：今晚关键词是{tags}。",
        f"在{names[0]}完成第一张合照或第一轮轻任务。" if names else "开场先完成一个轻任务。",
        f"收尾时每人说一个今晚最好笑/最回血的瞬间。",
    ]


def _friend_host_tips(option: PlanOption, request: UserRequest) -> list[str]:
    tips = [
        f"群里先发局名和集合时间，默认按 {request.party_size} 人估算。",
        "每站只留一个小任务，不要把朋友局变成打卡 KPI。",
    ]
    if option.estimated_cost_per_person > request.budget_per_person:
        tips.append("当前预估高于预算，预约前先确认替换项或 AA 上限。")
    else:
        tips.append("预约前确认人数和晚到成员，避免库存草稿失真。")
    return tips


def _couple_stage_key(option: PlanOption, request: UserRequest) -> str:
    if request.hard_constraints.get("hotel_wanted") or any(item.type == TimelineType.HOTEL for item in option.timeline_items):
        return "夜宿需求"
    if request.relationship_stage == "纪念日" or request.relationship_goal == "制造仪式感":
        return "纪念日"
    if request.relationship_stage == "想修复关系" or request.relationship_goal == "缓和关系":
        return "吵架后"
    if request.relationship_stage == "刚在一起":
        return "刚在一起"
    if request.relationship_stage == "暧昧/追求中":
        return "初识/暧昧"
    if request.relationship_goal == "自然升温":
        return "追求期"
    return "稳定期"


def _couple_signature_moments(option: PlanOption, stage: str) -> list[str]:
    names = [item.merchant_name for item in option.timeline_items[:3]]
    if stage == "纪念日":
        return ["提前准备一句纪念日开场白。", f"在{names[0]}留一张正式合照。" if names else "留一张正式合照。", "收尾时互相说一个今年最想记住的瞬间。"]
    if stage == "吵架后":
        return ["开场先不复盘争执，只确认今天想好好相处。", "中段用并肩走或安静吃饭降低对抗感。", "收尾只做一个小承诺，不现场拉扯结论。"]
    if stage == "夜宿需求":
        return ["夜宿只作为双方明确确认后的收尾。", "提前展示退款、隐私和安全规则。", "如果任一方犹豫，直接切换非夜宿版本。"]
    return ["开场用轻问题破冰，不急着进入关系判断。", f"在{names[1]}制造一个自然互动点。" if len(names) > 1 else "中段制造一个自然互动点。", "结束时留一句轻松的下次邀约。"]


def _couple_host_tips(option: PlanOption, request: UserRequest, stage: str) -> list[str]:
    tips = ["不要把路线排得太满，给迟到和情绪变化留 15 分钟缓冲。"]
    if stage == "初识/暧昧":
        tips.extend(["默认不安排酒店、过度私密空间或高压表白。", "结束时用轻松的下次铺垫，不逼问关系答案。"])
    elif stage == "吵架后":
        tips.extend(["地点优先安静、可并肩而坐，不选嘈杂高刺激项目。", "不要在第一站复盘矛盾，先恢复安全感。"])
    elif stage == "夜宿需求":
        tips.extend(["夜宿、支付和身份信息必须再次确认。", "保留非夜宿兜底方案，任何一方犹豫就切换。"])
    else:
        tips.extend(["餐厅优先选不催桌、方便自然聊天的位置。", "保留一个小仪式，但不要让对方有负担。"])
    if option.estimated_cost_per_person > request.budget_per_person:
        tips.append("当前预估高于预算，预约前先做替换或预算确认。")
    return tips


def _area_label(option: PlanOption) -> str:
    first = next((item.area_cluster for item in option.timeline_items if item.area_cluster), "")
    return f"{first.replace('_', ' ')} " if first else ""
