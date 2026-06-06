from __future__ import annotations


HANGZHOU_DEMO_VERSION = "hangzhou_seed_v1.4.0"


HANGZHOU_ROUTE_CLUSTERS: list[dict[str, object]] = [
    {"id": "hefang_old_town", "city": "hangzhou", "name": "河坊街/南宋御街", "transport_hint": "地铁到定安路或吴山广场后步行串联。"},
    {"id": "canal_qiaoxi", "city": "hangzhou", "name": "京杭大运河/桥西", "transport_hint": "桥西片区内步行友好，适合运河人文 Citywalk。"},
    {"id": "westlake_hubin", "city": "hangzhou", "name": "西湖湖滨", "transport_hint": "湖滨地铁可达，路线短，适合低体力打卡。"},
    {"id": "longwu_tea_hills", "city": "hangzhou", "name": "龙坞茶山", "transport_hint": "建议打车或自驾，片区内茶山、农家菜和茶室闭环。"},
    {"id": "xixi_wetland", "city": "hangzhou", "name": "西溪湿地", "transport_hint": "适合低体力近郊自然路线，雨天切良渚或武林室内。"},
    {"id": "liangzhu_culture", "city": "hangzhou", "name": "良渚文化", "transport_hint": "适合雨天人文路线，建议预留交通缓冲。"},
    {"id": "xianghu_lake", "city": "hangzhou", "name": "湘湖", "transport_hint": "适合近郊水岸轻松线，可作为龙坞/西溪的低体力替换。"},
    {"id": "wulin_kerry", "city": "hangzhou", "name": "武林/嘉里中心", "transport_hint": "地铁可达，雨天和低体力场景稳定。"},
]


HANGZHOU_THEME_TEMPLATES: list[dict[str, object]] = [
    {
        "id": "hz_old_town_fireworks",
        "city": "hangzhou",
        "name": "老城烟火半日局",
        "duration": "half_day",
        "route_cluster": "hefang_old_town",
        "experience_tags": ["老城烟火", "特色美食", "本土底蕴"],
        "description": "河坊街/南宋御街同片区吃、做、拍，适合没目标又想感受老杭州的人。",
        "version": "backend_v1.1.0",
    },
    {
        "id": "hz_canal_citywalk",
        "city": "hangzhou",
        "name": "运河人文 Citywalk",
        "duration": "half_day",
        "route_cluster": "canal_qiaoxi",
        "experience_tags": ["运河", "人文", "夜景"],
        "description": "桥西展馆、杭帮菜和河岸夜景串成一段水路故事。",
        "version": "backend_v1.1.0",
    },
    {
        "id": "hz_westlake_easy",
        "city": "hangzhou",
        "name": "西湖轻松打卡局",
        "duration": "half_day",
        "route_cluster": "westlake_hubin",
        "experience_tags": ["西湖", "打卡", "低体力"],
        "description": "保留湖滨轻逛、茶点和日落，不把西湖走成拉练。",
        "version": "backend_v1.1.0",
    },
    {
        "id": "hz_longwu_suburb",
        "city": "hangzhou",
        "name": "龙坞茶山近郊局",
        "duration": "full_day",
        "route_cluster": "longwu_tea_hills",
        "experience_tags": ["近郊山水", "茶山", "放松"],
        "description": "茶山轻走、农家菜和茶室收尾，周末换一口空气。",
        "version": "backend_v1.1.0",
    },
    {
        "id": "hz_food_tour",
        "city": "hangzhou",
        "name": "杭州特色美食巡游",
        "duration": "half_day",
        "route_cluster": "hefang_old_town",
        "experience_tags": ["特色美食", "老城烟火", "低预算"],
        "description": "把小吃、轻体验和街巷打卡做成一条边走边吃的路线。",
        "version": "backend_v1.1.0",
    },
    {
        "id": "hz_rainy_indoor",
        "city": "hangzhou",
        "name": "雨天室内低耗局",
        "duration": "half_day",
        "route_cluster": "wulin_kerry",
        "experience_tags": ["雨天室内", "低体力", "放松"],
        "description": "片儿川、室内手作和茶馆/足道把雨天稳稳接住。",
        "version": "backend_v1.1.0",
    },
]
