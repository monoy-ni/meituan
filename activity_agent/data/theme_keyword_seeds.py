from __future__ import annotations

from activity_agent.domain.models import Scene, Theme, UserRequest


FRIENDS_THEME_KEYWORD_SEEDS: dict[str, list[str]] = {
    "下班兄弟回血局": ["KTV", "烧烤", "酒吧"],
    "下班回血局": ["KTV", "烧烤", "酒吧"],
    "friends_recovery": ["KTV", "烧烤", "酒吧"],
    "发疯解压局": ["KTV", "拳击", "酒吧", "烧烤"],
    "friends_release": ["KTV", "拳击", "酒吧", "烧烤"],
    "低成本快乐局": ["小吃", "桌游", "夜宵"],
    "friends_budget": ["小吃", "桌游", "夜宵"],
    "出片聊天局": ["展览", "甜品", "咖啡"],
    "friends_photo_chat": ["展览", "甜品", "咖啡"],
    "城市副本局": ["密室", "剧本杀", "酒吧"],
    "friends_city_quest": ["密室", "剧本杀", "酒吧"],
}

HANGZHOU_THEME_KEYWORD_SEEDS: dict[str, list[str]] = {
    "杭州老城烟火半日局": ["小吃", "手作", "夜景"],
    "hz_old_town_fireworks": ["小吃", "手作", "夜景"],
    "运河人文 Citywalk": ["博物馆", "杭帮菜", "夜景"],
    "hz_canal_citywalk": ["博物馆", "杭帮菜", "夜景"],
    "西湖轻松打卡局": ["茶馆", "咖啡", "西湖景点"],
    "hz_westlake_easy": ["茶馆", "咖啡", "西湖景点"],
    "龙坞茶山近郊局": ["茶馆", "农家菜", "茶山"],
    "hz_longwu_suburb": ["茶馆", "农家菜", "茶山"],
    "杭州特色美食巡游": ["小吃", "杭帮菜", "夜宵"],
    "hz_food_tour": ["小吃", "杭帮菜", "夜宵"],
    "雨天室内低耗局": ["商场", "手作", "茶馆"],
    "hz_rainy_indoor": ["商场", "手作", "茶馆"],
}

COUPLE_THEME_KEYWORD_SEEDS: dict[str, list[str]] = {
    "轻升温不尴尬约会": ["手作", "甜品", "咖啡"],
    "couple_warmup": ["手作", "甜品", "咖啡"],
    "把普通周末过成小纪念日": ["手作", "西餐", "花店"],
    "couple_memory": ["手作", "西餐", "花店"],
    "关系修复缓冲约会": ["茶馆", "安静餐厅", "散步"],
    "couple_repair": ["茶馆", "安静餐厅", "散步"],
    "夜宿放松约会": ["手作", "西餐", "酒店"],
    "couple_overnight": ["手作", "西餐", "酒店"],
}

COUPLE_STAGE_KEYWORD_SEEDS: dict[str, list[str]] = {
    "暧昧/追求中": ["咖啡", "甜品", "轻手作"],
    "刚在一起": ["手作", "甜品", "散步"],
    "稳定情侣": ["西餐", "茶馆", "夜景"],
    "纪念日": ["手作", "西餐", "花店"],
    "想修复关系": ["茶馆", "安静餐厅", "散步"],
    "想制造惊喜": ["花店", "蛋糕", "西餐"],
}

COUPLE_GOAL_KEYWORD_SEEDS: dict[str, list[str]] = {
    "降低邀约门槛": ["咖啡", "甜品", "轻手作"],
    "降低尴尬": ["咖啡", "展览", "甜品"],
    "自然升温": ["手作", "甜品", "散步"],
    "创造共同体验": ["手作", "陶艺", "展览"],
    "增加浪漫感": ["西餐", "夜景", "花店"],
    "制造仪式感": ["西餐", "花店", "蛋糕"],
    "制造惊喜": ["花店", "蛋糕", "西餐"],
    "缓和关系": ["茶馆", "安静餐厅", "散步"],
    "夜宿闭环": ["西餐", "酒店", "酒吧"],
    "送礼表达": ["花店", "蛋糕", "手作"],
    "日常保鲜": ["咖啡", "展览", "甜品"],
}

THEME_KEYWORD_SEEDS: dict[str, list[str]] = {
    **FRIENDS_THEME_KEYWORD_SEEDS,
    **HANGZHOU_THEME_KEYWORD_SEEDS,
    **COUPLE_THEME_KEYWORD_SEEDS,
}

TAG_KEYWORD_SEEDS: dict[str, list[str]] = {
    "回血": ["KTV", "烧烤", "酒吧"],
    "回能量": ["KTV", "烧烤", "酒吧"],
    "解压": ["KTV", "拳击", "酒吧"],
    "发疯": ["KTV", "拳击", "酒吧"],
    "省钱": ["小吃", "桌游", "夜宵"],
    "出片": ["展览", "咖啡", "夜景"],
    "聊天": ["咖啡", "甜品", "茶馆"],
    "特色美食": ["小吃", "杭帮菜", "夜宵"],
    "雨天室内": ["商场", "手作", "茶馆"],
    "手作": ["陶艺", "银饰", "香薰"],
    "浪漫": ["西餐", "花店", "甜品"],
    "西湖": ["茶馆", "咖啡", "西湖景点"],
    "运河": ["博物馆", "杭帮菜", "夜景"],
}

DEFAULT_KEYWORD_SEEDS = ["美食", "游乐", "咖啡"]


def keyword_seeds_for_theme(theme: Theme, request: UserRequest | None = None) -> list[str]:
    seeds: list[str] = []
    if request and request.scene == Scene.COUPLE:
        seeds.extend(COUPLE_STAGE_KEYWORD_SEEDS.get(str(request.relationship_stage or ""), []))
        seeds.extend(COUPLE_GOAL_KEYWORD_SEEDS.get(str(request.relationship_goal or ""), []))
        seed_table = COUPLE_THEME_KEYWORD_SEEDS
    else:
        seed_table = FRIENDS_THEME_KEYWORD_SEEDS

    seed_table = {**seed_table, **HANGZHOU_THEME_KEYWORD_SEEDS}
    for key in (theme.id, theme.name):
        seeds.extend(seed_table.get(key, []))

    for tag in [*theme.trigger_tags, *theme.experience_tags, *(request.mood_tags if request else []), *(request.experience_tags if request else [])]:
        seeds.extend(TAG_KEYWORD_SEEDS.get(tag, []))
        for known_tag, known_seeds in TAG_KEYWORD_SEEDS.items():
            if known_tag and known_tag in tag:
                seeds.extend(known_seeds)

    return _unique(seeds)[:8] or list(DEFAULT_KEYWORD_SEEDS)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
