from __future__ import annotations

from activity_agent import ActivityPlanningAgent
from activity_agent.domain.models import Scene
from activity_agent.modules.theme_planner import ThemePlanner


def debug_repair():
    """调试关系修复的场景"""
    print("=" * 80)
    print("调试关系修复场景")
    print("=" * 80)
    
    test_input = "最近和女朋友吵架了，想找个安静地方缓和一下"
    print(f"\n用户输入: {test_input}")

    agent = ActivityPlanningAgent()
    theme_planner = ThemePlanner()

    # 1. 分析需求
    print("\n--- Step 1: Intent Router ---")
    route = agent.intent_router.route(test_input, scene_hint=Scene.COUPLE)
    print(f"Route: {route}")
    
    print("\n--- Step 2: Context Collector ---")
    request, missing_questions, assumptions = agent.context_collector.collect(route, test_input)
    
    print(f"Scene: {request.scene}")
    print(f"Relationship Stage: {request.relationship_stage}")
    print(f"Relationship Goal: {request.relationship_goal}")
    print(f"Mood Tags: {request.mood_tags}")
    print(f"Experience Tags: {request.experience_tags}")
    
    # 2. 测试各个主题的评分
    print("\n--- Step 3: Theme Scores ---")
    
    from activity_agent.modules.theme_planner import COUPLE_THEMES
    print("情侣主题评分:")
    for theme in COUPLE_THEMES:
        score = theme_planner._score_couple(theme, request)
        print(f"  - {theme.name} ({theme.id}): {score}")
        print(f"    stages: {theme.stages}, goals: {theme.goals}")

    # 3. 最终选择
    print("\n--- Step 4: Final Themes ---")
    themes = theme_planner.plan(request)
    for i, theme in enumerate(themes[:3]):
        print(f"  {i+1}. {theme.name} ({theme.id})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    debug_repair()
