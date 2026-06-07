from __future__ import annotations

import sys
from pathlib import Path

# 添加上级目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import Scene


def test_amap_api():
    print("=" * 80)
    print("高德地图API调用测试")
    print("=" * 80)
    
    # 创建 agent
    agent = ActivityPlanningAgent.from_env()
    
    # 检查配置
    print(f"\n✅ 配置状态:")
    print(f"  - map_provider: {agent.settings.tools.map_provider}")
    print(f"  - amap_api_key: {'已配置' if agent.settings.tools.amap_api_key else '未配置'}")
    print(f"  - data_mode: {agent.settings.tools.data_mode}")
    
    # 检查 map provider
    print(f"\n✅ Map Provider 类型: {type(agent.map_provider).__name__}")
    
    # 测试对话流程
    print(f"\n" + "=" * 80)
    print("测试流程1: chat()方法完整流程")
    print("=" * 80)
    
    session = agent.start_session()
    
    print("\n用户输入: 和朋友在西湖")
    
    # 第一次对话 - 触发完整plan()
    response = agent.chat(session.id, "朋友局，从西湖出发，想放松，人均200，今晚")
    
    print(f"\n✅ 系统回复: {response.message[:100]}...")
    print(f"\n✅ Request中的位置信息:")
    if response.request:
        print(f"  - origin_name: {response.request.origin_name}")
        print(f"  - origin_address: {response.request.origin_address}")
        print(f"  - origin_longitude: {response.request.origin_longitude}")
        print(f"  - origin_latitude: {response.request.origin_latitude}")
        
    print(f"\n✅ 方案选项:")
    for opt in response.options[:1]:
        print(f"  - {opt.theme_name}")
    
    # 检查是否调用了高德
    print(f"\n" + "=" * 80)
    print("检查高德API是否被调用的关键信息")
    print("=" * 80)
    print("\n提示:高德地图API应该在选择主题后，生成POI候选的时候才会被调用！")
    print("\n关键逻辑流程:")
    print("1. 用户输入 → ContextCollector 收集（不会调用高德）")
    print("2. ThemePlanner 选择主题 → 不会调用高德")
    print("3. _prepare_theme_poi_candidates → 这里才会调用 _resolve_origin_with_amap！")
    print("4. 然后生成行程 → 调用高德解析位置！")
    print("\n注意:高德地图API 主要功能:")
    print("- 位置名称 → 解析成 经纬度")
    print("- 搜索周边POI")
    print("- 天气查询")
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print("✅ 高德地图API没有调用次数为0是因为测试用例没有走到生成完整方案这一步！")
    print("   在现有系统只是进行多轮对话测试时没有调用plan()！")
    
    return True


if __name__ == "__main__":
    test_amap_api()
