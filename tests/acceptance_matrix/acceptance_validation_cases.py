from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AcceptanceCase:
    case_id: str
    title: str
    category: str
    requirement: str
    description: str
    related_files: list[str] = field(default_factory=list)


def build_acceptance_cases() -> list[AcceptanceCase]:
    return [
        AcceptanceCase(
            case_id="AC-01",
            title="AI 多轮交流确认主题",
            category="主题确认",
            requirement="AI 与用户进行交流确认主题，信息足够后再生成方案。",
            description="覆盖模糊开场、场景确认、玩法氛围、预算、时间、默认集合点/距离确认和最终出方案。",
            related_files=[
                "activity_agent/modules/dialogue_manager.py",
                "activity_agent/agent.py",
                "tests/acceptance_matrix/scenario_01_theme_confirmation/test_theme_confirmation_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-02",
            title="集合位置、高德 IP 定位与默认位置",
            category="位置确认",
            requirement="用户信息中需要包括集合位置；支持高德 IP 定位；用户不给位置时默认奥映世纪轩。",
            description="覆盖高德 /ip client 参数、默认集合点名称、地址、高德链接和默认坐标。",
            related_files=[
                "activity_agent/providers/live_sources.py",
                "activity_agent/domain/models.py",
                "activity_agent/modules/context_collector.py",
                "tests/acceptance_matrix/scenario_02_location_amap_ip_default/test_location_amap_ip_default_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-03",
            title="距离要求与整体路径要求",
            category="距离约束",
            requirement="询问用户对距离和整体行程路径长短的要求，并写入最终请求。",
            description="覆盖默认距离提示、用户自定义集合点、周边搜索范围、路线公里数和路线分钟数。",
            related_files=[
                "activity_agent/modules/dialogue_manager.py",
                "activity_agent/agent.py",
                "tests/acceptance_matrix/scenario_03_distance_and_route_requirements/test_distance_route_requirements_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-04",
            title="高德 POI 范围搜索",
            category="POI 搜索",
            requirement="通过高德 POI 在用户给出范围内搜索美食和游乐地点。",
            description="覆盖 around location、半径换算、餐饮/游乐关键词、POI 入库和 matched_keywords。",
            related_files=[
                "activity_agent/providers/live_sources.py",
                "activity_agent/agent.py",
                "tests/acceptance_matrix/scenario_04_amap_poi_range_search/test_amap_poi_range_search_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-05",
            title="mock 美团评价与 LLM 商户组合",
            category="商户组合",
            requirement="mock 调用美团用户评价和商户介绍，让 LLM 获取适合主题局的商铺、饭店、景点等并组合完整主题局。",
            description="覆盖 mock 商户画像、LLM prompt、过滤编造商户 ID、按主题 slots 组合路线。",
            related_files=[
                "activity_agent/tools/mock_meituan.py",
                "activity_agent/llm/itinerary_curator.py",
                "activity_agent/modules/supply_matcher.py",
                "activity_agent/modules/itinerary_composer.py",
                "tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection/test_meituan_profiles_llm_selection_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-06",
            title="高德路径规划",
            category="路径规划",
            requirement="调用高德地图 API 的路径规划工具，给出用户游玩路径。",
            description="覆盖每段 walking_route 调用、route_plan legs、总距离、总时长和 within_limits。",
            related_files=[
                "activity_agent/agent.py",
                "activity_agent/providers/live_sources.py",
                "tests/acceptance_matrix/scenario_06_amap_route_planning/test_amap_route_planning_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-07",
            title="情侣/朋友 skill 体验卡",
            category="体验卡",
            requirement="情侣使用 couple-date-designer，朋友使用 themed-outing-designer，生成完整的局卡片。",
            description="覆盖 designer 字段、卡片必要字段、flow 与 timeline 对齐、预约安全说明。",
            related_files=[
                "activity_agent/modules/experience_card_designer.py",
                "skill/couple-date-designer/SKILL.md",
                "skill/themed-outing-designer/SKILL.md",
                "tests/acceptance_matrix/scenario_07_skill_experience_cards/test_skill_experience_cards_acceptance.py",
            ],
        ),
        AcceptanceCase(
            case_id="AC-08",
            title="mock 美团预约与下单",
            category="预约下单",
            requirement="mock 调用美团 API 完成预约和下单验证，同时保持确认前安全边界。",
            description="覆盖可用性检查、booking hold、AA 草稿、取消不下单、确认后生成 mock 订单。",
            related_files=[
                "activity_agent/tools/mock_meituan.py",
                "activity_agent/modules/booking_orchestrator.py",
                "activity_agent/agent.py",
                "tests/acceptance_matrix/scenario_08_mock_booking_order/test_mock_booking_order_acceptance.py",
            ],
        ),
    ]
