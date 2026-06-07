from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from activity_agent.config import AgentSettings


def test_env_config():
    print("=" * 80)
    print("检查环境配置")
    print("=" * 80)
    
    settings = AgentSettings.from_env()
    
    print(f"\nMap Provider: {settings.tools.map_provider}")
    print(f"AMAP API Key: {'已配置' if settings.tools.amap_api_key else '未配置'}")
    if settings.tools.amap_api_key:
        print(f"  开头: {settings.tools.amap_api_key[:10]}...")
    print(f"Data Mode: {settings.tools.data_mode}")
    print(f"AMAP City: {settings.tools.amap_city}")
    
    return settings


def test_amap_client():
    print("\n" + "=" * 80)
    print("测试高德地图API客户端")
    print("=" * 80)
    
    try:
        from activity_agent.providers.live_sources import AmapWebServiceClient
        
        settings = AgentSettings.from_env()
        
        if not settings.tools.amap_api_key:
            print("\n❌ 没有配置 AMAP_API_KEY！")
            return False
        
        print(f"\n创建高德地图客户端...")
        
        client = AmapWebServiceClient(settings.tools.amap_api_key)
        
        print(f"✅ 客户端创建成功！")
        
        print(f"\n测试位置解析...")
        # 测试解析"西湖"
        result = client.resolve_location(settings.tools.amap_city, "西湖")
        
        if result:
            print(f"✅ 位置解析成功！")
            print(f"\n结果:")
            for k, v in result.items():
                print(f"  {k}: {v}")
        else:
            print(f"❌ 位置解析失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_build_map_provider():
    print("\n" + "=" * 80)
    print("测试地图Provider构建")
    print("=" * 80)
    
    try:
        from activity_agent import ActivityPlanningAgent
        
        agent = ActivityPlanningAgent.from_env()
        
        print(f"\nMap Provider: {type(agent.map_provider).__name__}")
        
        if "Amap" in type(agent.map_provider).__name__:
            print(f"✅ 正在使用高德地图API！")
        else:
            print(f"⚠️ 使用的是Mock地图Provider")
            print(f"   原因:检查 _use_amap 条件")
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    print("\n高德地图API完整测试")
    print("=" * 80)
    
    all_good = True
    
    # 1. 测试环境配置
    test_env_config()
    
    # 2. 测试API客户端
    if not test_amap_client():
        all_good = False
    
    # 3. 测试Provider
    test_build_map_provider()
    
    print("\n" + "=" * 80)
    if all_good:
        print("✅ 所有测试通过！高德地图API配置正常！")
    else:
        print("❌ 有测试失败")
    print("=" * 80)
    
    print("\n重要说明:")
    print("高德地图API的调用时机:")
    print("1. 只有在 plan() 方法中，准备主题POI候选时才会调用")
    print("2. 在 _prepare_theme_poi_candidates → _resolve_origin_with_amap 中调用")
    print("3. 简单的多轮对话收集阶段不会调用高德API")


if __name__ == "__main__":
    main()
