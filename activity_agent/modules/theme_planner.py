from __future__ import annotations

from activity_agent.domain.models import Scene, Theme, ThemeSlot, TimelineType, UserRequest


FRIENDS_THEMES: list[Theme] = [
    Theme(
        id="friends_recovery",
        name="下班回血局",
        emotional_hook="今晚别直接回家，把班味洗掉。",
        trigger_tags=["回血", "养生"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["运动", "回血", "室内"], "把压力先丢出去"),
            ThemeSlot(TimelineType.DINING, ["烤肉", "回血", "多巴胺"], "认真补充多巴胺"),
            ThemeSlot(TimelineType.RELAX, ["洗浴", "放松", "回血"], "一键进入低电量恢复模式"),
        ],
        add_ons=["预估 AA", "局后照片合辑", "下次轻徒步推荐"],
    ),
    Theme(
        id="friends_budget",
        name="低成本快乐局",
        emotional_hook="少花点钱，也能给这周留一个好笑的晚上。",
        trigger_tags=["省钱", "低耗社交"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["省钱", "轻松", "室内"], "用轻内容打开话题"),
            ThemeSlot(TimelineType.DINING, ["夜市", "省钱"], "边走边吃，不用正襟危坐"),
            ThemeSlot(TimelineType.NIGHTLIFE, ["省钱", "热闹", "不喝酒"], "有人晚到也能接上"),
        ],
        add_ons=["便宜替换项", "活动后补差价 AA", "朋友圈文案"],
    ),
    Theme(
        id="friends_photo_chat",
        name="出片聊天局",
        emotional_hook="不是吃饭，是一起存一段能发出去的城市回忆。",
        trigger_tags=["出片", "聊天"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["出片", "审美", "聊天"], "先给今晚一个画面感"),
            ThemeSlot(TimelineType.DINING, ["甜品", "聊天", "出片"], "把话题接住"),
            ThemeSlot(TimelineType.RELAX, ["夜景", "散步", "不喝酒"], "轻轻收尾，不赶路"),
        ],
        add_ons=["出片点提示", "朋友圈文案", "下次展览提醒"],
    ),
    Theme(
        id="friends_release",
        name="发疯解压局",
        emotional_hook="周五发疯合法化，不聊 KPI，只把压力打出去。",
        trigger_tags=["发疯", "解压"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["发疯", "解压", "运动"], "先释放压力"),
            ThemeSlot(TimelineType.DINING, ["烤肉", "热闹"], "补回能量"),
            ThemeSlot(TimelineType.NIGHTLIFE, ["发疯", "热闹"], "把快乐延长一点"),
        ],
        add_ons=["KTV 替换", "不喝酒版本", "预估 AA"],
    ),
    Theme(
        id="friends_city_quest",
        name="城市副本局",
        emotional_hook="给普通夜晚开一个城市副本，直接跟着走。",
        trigger_tags=["新鲜"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["新鲜", "出片", "室内"], "先进入副本"),
            ThemeSlot(TimelineType.DINING, ["氛围", "聊天"], "交换刚刚的体验"),
            ThemeSlot(TimelineType.NIGHTLIFE, ["多巴胺", "热闹"], "收一个强记忆点"),
        ],
        add_ons=["可换成不喝酒", "转发群聊", "下次副本推荐"],
    ),
]

COUPLE_THEMES: list[Theme] = [
    Theme(
        id="couple_warmup",
        name="轻升温不尴尬约会",
        emotional_hook="不是表白局，是一次让 TA 觉得和你待着很舒服的轻约会。",
        stages=["暧昧/追求中", "刚在一起"],
        goals=["降低邀约门槛", "降低尴尬", "自然升温"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["轻互动", "安全", "室内"], "用轻互动破冰"),
            ThemeSlot(TimelineType.DINING, ["甜品", "安全", "聊天"], "在好退出的地方继续聊"),
            ThemeSlot(TimelineType.RELAX, ["散步", "夜景", "留白"], "状态好就散步，累了就体面结束"),
        ],
        add_ons=["低压力邀约话术", "体面结束话术", "下次邀约铺垫"],
    ),
    Theme(
        id="couple_memory",
        name="把普通周末过成小纪念日",
        emotional_hook="把普通周末过成只属于你们的小纪念日。",
        stages=["稳定情侣", "纪念日", "想制造惊喜"],
        goals=["创造共同体验", "制造仪式感", "增加浪漫感", "制造惊喜"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["手作", "纪念", "浪漫"], "共同完成一个小作品"),
            ThemeSlot(TimelineType.DINING, ["浪漫", "安静", "仪式感"], "认真吃一顿有氛围的饭"),
            ThemeSlot(TimelineType.RELAX, ["夜景", "散步", "浪漫"], "不赶路，只认真待在一起"),
        ],
        add_ons=["花束", "蛋糕", "双人回忆卡", "纪念日提醒"],
    ),
    Theme(
        id="couple_repair",
        name="关系修复缓冲约会",
        emotional_hook="不用急着讲道理，先一起把情绪放下来。",
        stages=["想修复关系"],
        goals=["缓和关系"],
        slots=[
            ThemeSlot(TimelineType.RELAX, ["放松", "安静", "不喝酒"], "先降低情绪强度"),
            ThemeSlot(TimelineType.DINING, ["安静", "聊天", "安全"], "选择不吵的地方慢慢说"),
            ThemeSlot(TimelineType.RELAX, ["散步", "留白", "夜景"], "给和好留一点空间"),
        ],
        add_ons=["道歉话术", "冲突降温提醒", "不安排高刺激项目"],
    ),
    Theme(
        id="couple_overnight",
        name="夜宿放松约会",
        emotional_hook="不赶路、不排队、不做攻略，只认真待在一起。",
        stages=["稳定情侣", "纪念日"],
        goals=["夜宿闭环", "增加浪漫感"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["手作", "浪漫"], "先做一个共同体验"),
            ThemeSlot(TimelineType.DINING, ["浪漫", "安静"], "用晚餐进入放松节奏"),
            ThemeSlot(TimelineType.HOTEL, ["酒店", "泡汤", "隐私"], "双方都确认后再进入夜宿闭环"),
        ],
        add_ons=["酒店安全提示", "双人早餐", "花束/蛋糕小时达"],
    ),
]


class ThemePlanner:
    """Turns mood and relationship tasks into three actionable theme directions."""

    def plan(self, request: UserRequest) -> list[Theme]:
        if request.scene == Scene.COUPLE:
            scored = [(theme, self._score_couple(theme, request)) for theme in COUPLE_THEMES]
        else:
            scored = [(theme, self._score_friends(theme, request)) for theme in FRIENDS_THEMES]
        return [theme for theme, _ in sorted(scored, key=lambda pair: pair[1], reverse=True)[:3]]

    def _score_friends(self, theme: Theme, request: UserRequest) -> int:
        score = 3 * len(set(theme.trigger_tags) & set(request.mood_tags))
        if request.hard_constraints.get("cheaper") and theme.id == "friends_budget":
            score += 4
        if request.hard_constraints.get("photo_friendly") and theme.id == "friends_photo_chat":
            score += 4
        if request.hard_constraints.get("no_alcohol") and theme.id in {"friends_budget", "friends_photo_chat"}:
            score += 2
        return score

    def _score_couple(self, theme: Theme, request: UserRequest) -> int:
        score = 0
        if request.relationship_stage in theme.stages:
            score += 4
        if request.relationship_goal in theme.goals:
            score += 4
        if request.hard_constraints.get("hotel_wanted") and theme.id == "couple_overnight":
            score += 10
        if request.hard_constraints.get("gift_wanted") and theme.id == "couple_memory":
            score += 3
        if request.relationship_stage == "暧昧/追求中" and theme.id == "couple_overnight":
            score -= 99
        return score
