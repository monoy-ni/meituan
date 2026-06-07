from __future__ import annotations

from activity_agent.domain import Scene

from tests.location_confirmation_harness import (
    LocationTestCase,
    LocationConfirmationTurn,
    DEFAULT_LOCATION,
    DEFAULT_ADDRESS,
    DEFAULT_AMAP_URL,
    DEFAULT_LONGITUDE,
    DEFAULT_LATITUDE,
)


def build_location_test_cases() -> list[LocationTestCase]:
    return [
        # ============ 场景1: 用户明确给出位置 ============
        LocationTestCase(
            case_id="LOC-01",
            title="用户明确给出集合点: 西湖",
            category="信息明确",
            description="用户在首次对话中明确给出集合位置为西湖",
            turns=[
                LocationConfirmationTurn("朋友局，从西湖出发", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想放松，人均200"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="西湖",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        LocationTestCase(
            case_id="LOC-02",
            title="用户明确给出集合点: 河坊街",
            category="信息明确",
            description="用户在首次对话中明确给出集合位置为河坊街",
            turns=[
                LocationConfirmationTurn("情侣约会，在河坊街", scene_hint=Scene.COUPLE),
                LocationConfirmationTurn("想浪漫一点，人均300"),
                LocationConfirmationTurn("周六下午"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="河坊街",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景2: 用户未给出位置，使用默认值 ============
        LocationTestCase(
            case_id="LOC-03",
            title="用户未给出位置，使用默认值奥映世纪轩",
            category="默认值",
            description="用户全程未提到位置，系统使用默认位置",
            turns=[
                LocationConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想放松，人均180"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location=DEFAULT_LOCATION,
            expected_final_address=DEFAULT_ADDRESS,
            expected_amap_url=DEFAULT_AMAP_URL,
            expected_longitude=DEFAULT_LONGITUDE,
            expected_latitude=DEFAULT_LATITUDE,
            expected_uses_default=True,
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景3: 位置信息在后续轮次补充 ============
        LocationTestCase(
            case_id="LOC-04",
            title="位置信息在第三轮补充",
            category="信息补充",
            description="用户前两轮未提位置，第三轮明确给出",
            turns=[
                LocationConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想放松，人均150"),
                LocationConfirmationTurn("从西溪湿地附近出发"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="西溪湿地",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景4: 模糊位置描述 ============
        LocationTestCase(
            case_id="LOC-05",
            title="用户给出模糊位置描述: 地铁6号线附近",
            category="模糊信息",
            description="用户位置描述比较模糊，依赖系统解析",
            turns=[
                LocationConfirmationTurn("朋友局，地铁6号线附近", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想拍照，人均220"),
                LocationConfirmationTurn("周末"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景5: 包含完整地址 ============
        LocationTestCase(
            case_id="LOC-06",
            title="用户给出完整地址: 民祥路与平澜路交汇处",
            category="详细地址",
            description="用户给出完整的街道地址",
            turns=[
                LocationConfirmationTurn("情侣约会，在民祥路与平澜路交汇处", scene_hint=Scene.COUPLE),
                LocationConfirmationTurn("想轻松一点，人均260"),
                LocationConfirmationTurn("周日下午"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location=DEFAULT_LOCATION,
            expected_final_address=DEFAULT_ADDRESS,
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景6: 提及地铁出口 ============
        LocationTestCase(
            case_id="LOC-07",
            title="用户给出地铁出口: 丰北站C出口",
            category="地铁位置",
            description="用户指定具体的地铁出口作为集合点",
            turns=[
                LocationConfirmationTurn("朋友局，丰北站C出口", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想唱歌，人均180"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location=DEFAULT_LOCATION,
            expected_final_address=DEFAULT_ADDRESS,
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景7: 位置+搜索半径 ============
        LocationTestCase(
            case_id="LOC-08",
            title="用户同时给出位置和搜索半径",
            category="高级配置",
            description="用户同时指定位置和搜索范围",
            turns=[
                LocationConfirmationTurn("朋友局，从武林广场出发，周边3公里", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想吃饭，人均200"),
                LocationConfirmationTurn("周末"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="武林广场",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景8: 位置修正 ============
        LocationTestCase(
            case_id="LOC-09",
            title="用户中途修正位置",
            category="信息修正",
            description="用户先给出一个位置，然后又更改了位置",
            turns=[
                LocationConfirmationTurn("朋友局，从西湖文化广场出发", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("不对，改到武林广场吧"),
                LocationConfirmationTurn("人均160"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="武林广场",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景9: 多场景位置一致性 ============
        LocationTestCase(
            case_id="LOC-10",
            title="情侣场景默认位置",
            category="跨场景",
            description="验证情侣场景默认位置也正常工作",
            turns=[
                LocationConfirmationTurn("情侣约会", scene_hint=Scene.COUPLE),
                LocationConfirmationTurn("想浪漫，人均350"),
                LocationConfirmationTurn("周六晚上"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location=DEFAULT_LOCATION,
            expected_final_address=DEFAULT_ADDRESS,
            expected_uses_default=True,
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景10: 复杂位置描述 ============
        LocationTestCase(
            case_id="LOC-11",
            title="复杂位置描述: 结合多个地标",
            category="复杂描述",
            description="用户给出比较复杂的位置描述，包含多个参考点",
            turns=[
                LocationConfirmationTurn("朋友局，在西湖文化广场和武林广场中间", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("人均180，想拍照"),
                LocationConfirmationTurn("周末下午"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景11: 纯地址无场景提示 ============
        LocationTestCase(
            case_id="LOC-12",
            title="用户只给位置不给场景提示",
            category="混合输入",
            description="用户首次对话只给位置信息，需要系统先识别场景",
            turns=[
                LocationConfirmationTurn("从龙坞出发"),
                LocationConfirmationTurn("朋友局"),
                LocationConfirmationTurn("人均200，想喝茶"),
                LocationConfirmationTurn("周末"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location="龙坞",
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
        
        # ============ 场景12: 高德地图URL测试 ============
        LocationTestCase(
            case_id="LOC-13",
            title="验证默认位置的高德URL",
            category="高德URL",
            description="验证默认位置的高德地图分享URL是否正确",
            turns=[
                LocationConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("想放松，人均180"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_location=DEFAULT_LOCATION,
            expected_amap_url=DEFAULT_AMAP_URL,
            expected_uses_default=True,
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=3,
        ),
    ]
