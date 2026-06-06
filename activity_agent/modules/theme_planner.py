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

HANGZHOU_CITY_THEMES: list[Theme] = [
    Theme(
        id="hz_old_town_fireworks",
        name="杭州老城烟火半日局",
        emotional_hook="不用查攻略，沿着河坊街和南宋御街吃、做、拍，把杭州老城的烟火气走成一个闭环。",
        trigger_tags=["杭州", "老城烟火", "特色美食", "本土底蕴", "低费脑"],
        journey_duration="half_day",
        route_story="先用老城小吃开胃，再做一个轻手作，最后用吴山夜景收住。",
        experience_tags=["老城烟火", "特色美食", "本土底蕴"],
        effort_level="低",
        transport_summary="河坊街/南宋御街同片区步行串联，少折返。",
        gain_points=["杭州老城味道", "可带走的手作记忆", "低预算夜景收尾"],
        checkin_points=["南宋御街门头", "河坊街小吃摊", "吴山夜景"],
        fallbacks=["下雨时把吴山夜景换成室内茶馆", "预算紧张时保留小吃巡游和免费打卡点", "手作满员时换成老街展陈"],
        slots=[
            ThemeSlot(TimelineType.DINING, ["杭州", "老城烟火", "特色美食", "小吃"], "先用老城小吃打开胃口", ["hefang_old_town"]),
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "老城", "手作", "人文", "室内"], "做一个能带走的老城体验", ["hefang_old_town"]),
            ThemeSlot(TimelineType.CHECKIN, ["杭州", "老城", "夜景", "打卡"], "用夜景或街巷照片收尾", ["hefang_old_town"]),
        ],
        add_ons=["老城拍照点", "低预算替换", "雨天室内替换"],
    ),
    Theme(
        id="hz_canal_citywalk",
        name="运河人文 Citywalk",
        emotional_hook="把运河边的展馆、杭帮菜和水岸夜景串起来，不是逛街，是走一段杭州水路故事。",
        trigger_tags=["杭州", "运河", "人文", "Citywalk", "夜景"],
        journey_duration="half_day",
        route_story="先看桥西展陈，再吃杭帮菜，最后沿大运河散步看夜景。",
        experience_tags=["运河", "人文", "夜景"],
        effort_level="中",
        transport_summary="桥西片区步行友好，适合半日慢走。",
        gain_points=["运河本土底蕴", "一顿杭帮菜", "河岸夜景记忆点"],
        checkin_points=["桥西老厂房", "运河桥洞", "河岸夜景"],
        fallbacks=["下雨时保留展馆和餐厅，取消河岸散步", "走累时把夜景换成茶饮", "餐厅满员时换同片区杭帮小馆"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "运河", "人文", "室内"], "先进入运河故事", ["canal_qiaoxi"]),
            ThemeSlot(TimelineType.DINING, ["杭州", "杭帮菜", "特色美食", "运河"], "用本地味道接住体验", ["canal_qiaoxi"]),
            ThemeSlot(TimelineType.CHECKIN, ["杭州", "运河", "夜景", "散步"], "沿河岸留下收尾画面", ["canal_qiaoxi"]),
        ],
        add_ons=["雨天室内版", "低体力版", "夜景拍照点"],
    ),
    Theme(
        id="hz_westlake_easy",
        name="西湖轻松打卡局",
        emotional_hook="不把西湖走成拉练，只保留湖滨轻逛、茶点和日落留白。",
        trigger_tags=["杭州", "西湖", "打卡", "出片", "低体力"],
        journey_duration="half_day",
        route_story="湖滨轻逛进入杭州感，茶点补能，再把日落留给聊天和拍照。",
        experience_tags=["西湖", "出片", "低体力"],
        effort_level="低",
        transport_summary="湖滨/南山路短线步行，适合不想太累。",
        gain_points=["经典杭州画面", "低体力路线", "茶点和日落"],
        checkin_points=["湖滨沿线", "南山路梧桐", "西湖日落"],
        fallbacks=["下雨时换湖滨茶点和室内展馆", "人多时绕开核心码头", "预算低时保留免费湖边线"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "西湖", "低体力", "出片"], "轻松进入西湖画面", ["westlake_hubin"]),
            ThemeSlot(TimelineType.DINING, ["杭州", "西湖", "茶点", "轻食"], "用茶点补能不拖节奏", ["westlake_hubin"]),
            ThemeSlot(TimelineType.CHECKIN, ["杭州", "西湖", "日落", "打卡"], "把日落留给照片和聊天", ["westlake_hubin"]),
        ],
        add_ons=["日落提醒", "雨天替换", "少走路版本"],
    ),
    Theme(
        id="hz_longwu_suburb",
        name="龙坞茶山近郊局",
        emotional_hook="不用硬爬山，去龙坞用茶山、农家菜和茶室给周末换一口空气。",
        trigger_tags=["杭州", "近郊山水", "茶山", "龙井", "放松", "低体力"],
        journey_duration="full_day",
        route_story="先茶山轻走，再吃茶香农家菜，最后在山脚茶室慢下来。",
        experience_tags=["近郊山水", "茶山", "放松", "低体力"],
        effort_level="中",
        transport_summary="建议打车或自驾，片区内完成闭环。",
        gain_points=["近郊空气感", "茶山照片", "农家菜和茶歇"],
        checkin_points=["茶垄远景", "山脚茶席", "农家菜院落"],
        fallbacks=["下雨时茶山轻徒步换茶室", "体力不足时缩短步行线或切湘湖/西溪低体力线", "预算紧张时保留茶山和农家菜"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "近郊山水", "茶山", "轻徒步"], "用低强度茶山进入近郊感", ["longwu_tea_hills"]),
            ThemeSlot(TimelineType.DINING, ["杭州", "近郊山水", "农家菜", "茶香"], "用热菜补足获得感", ["longwu_tea_hills"]),
            ThemeSlot(TimelineType.RELAX, ["杭州", "茶室", "放松", "聊天"], "用茶室慢慢收尾", ["longwu_tea_hills"]),
        ],
        add_ons=["打车建议", "雨天茶室版", "少走路版"],
    ),
    Theme(
        id="hz_food_tour",
        name="杭州特色美食巡游",
        emotional_hook="不纠结去哪家，把杭州小吃、手作和街巷打卡做成一条能边走边吃的路线。",
        trigger_tags=["杭州", "特色美食", "小吃", "老城烟火", "省钱", "低预算"],
        journey_duration="half_day",
        route_story="先吃小吃巡游，再插一个轻体验，最后用街巷或夜景收尾。",
        experience_tags=["特色美食", "老城烟火", "低预算"],
        effort_level="中",
        transport_summary="老城为主，必要时延伸到武林片区。",
        gain_points=["杭州小吃一次吃全", "低预算但完整", "街巷打卡"],
        checkin_points=["小吃摊", "老街招牌", "夜景收尾点"],
        fallbacks=["排队太长时切片儿川小馆", "下雨时改室内市集", "吃太饱时取消后续正餐"],
        slots=[
            ThemeSlot(TimelineType.DINING, ["杭州", "特色美食", "小吃", "老城烟火"], "先用杭州小吃巡游开局", ["hefang_old_town"]),
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "手作", "市集", "轻逛"], "用轻体验留出消化时间", ["hefang_old_town", "wulin_kerry"]),
            ThemeSlot(TimelineType.CHECKIN, ["杭州", "打卡", "夜景", "老城"], "用低成本照片收尾", ["hefang_old_town"]),
        ],
        add_ons=["低预算版", "排队替换", "雨天室内版"],
    ),
    Theme(
        id="hz_rainy_indoor",
        name="雨天室内低耗局",
        emotional_hook="下雨也不用回家躺平，用片儿川、室内手作和茶馆把一天稳稳接住。",
        trigger_tags=["杭州", "雨天室内", "室内", "低体力", "不想太累"],
        journey_duration="half_day",
        route_story="热乎吃一口，室内做点东西，最后用茶馆或足道恢复体力。",
        experience_tags=["雨天室内", "低体力", "放松"],
        effort_level="低",
        transport_summary="武林/嘉里中心为主，地铁友好，少淋雨。",
        gain_points=["雨天不空过", "低体力放松", "有杭州味的小体验"],
        checkin_points=["老面馆门头", "手作过程", "窗边茶席"],
        fallbacks=["手作满员时换室内市集", "想更放松时把茶馆换足道", "预算紧张时保留片儿川和市集"],
        slots=[
            ThemeSlot(TimelineType.DINING, ["杭州", "特色美食", "片儿川", "雨天可去"], "先用热乎杭州味开局", ["wulin_kerry"]),
            ThemeSlot(TimelineType.ACTIVITY, ["杭州", "室内", "雨天可去", "手作", "市集"], "雨天也保留参与感", ["wulin_kerry", "liangzhu_culture"]),
            ThemeSlot(TimelineType.RELAX, ["杭州", "茶馆", "放松", "低体力"], "用室内放松收尾", ["wulin_kerry"]),
        ],
        add_ons=["低预算版", "更放松版", "少走路版"],
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
        if self._is_hangzhou_day_out(request):
            scored = [(theme, self._score_hangzhou(theme, request)) for theme in HANGZHOU_CITY_THEMES]
            return [theme for theme, _ in sorted(scored, key=lambda pair: pair[1], reverse=True)[:3]]
        if request.scene == Scene.COUPLE:
            scored = [(theme, self._score_couple(theme, request)) for theme in COUPLE_THEMES]
        else:
            scored = [(theme, self._score_friends(theme, request)) for theme in FRIENDS_THEMES]
        return [theme for theme, _ in sorted(scored, key=lambda pair: pair[1], reverse=True)[:3]]

    def _is_hangzhou_day_out(self, request: UserRequest) -> bool:
        city_tags = {
            "杭州",
            "老城烟火",
            "运河",
            "西湖",
            "茶山",
            "近郊山水",
            "特色美食",
            "雨天室内",
            "低费脑",
            "不想查攻略",
            "本土底蕴",
        }
        return "hangzhou" in request.location_anchor.lower() or bool(city_tags & set(request.experience_tags))

    def _score_hangzhou(self, theme: Theme, request: UserRequest) -> int:
        request_tags = set([*request.experience_tags, *request.mood_tags])
        score = 5 * len(set(theme.trigger_tags) & request_tags)
        score += 4 * len(set(theme.experience_tags) & request_tags)
        if request.journey_duration == theme.journey_duration:
            score += 3
        if request.weather_sensitive and "雨天室内" in theme.experience_tags:
            score += 8
        if request.hard_constraints.get("cheaper") and "低预算" in theme.trigger_tags:
            score += 4
        if request.hard_constraints.get("photo_friendly") and any(tag in theme.experience_tags for tag in ["西湖", "出片"]):
            score += 3
        if request.hard_constraints.get("indoor_only") and "雨天室内" in theme.experience_tags:
            score += 5
        return score

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
