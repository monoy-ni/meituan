from __future__ import annotations

from pathlib import Path
from typing import Any
import json
from dataclasses import dataclass

from activity_agent import ActivityPlanningAgent
from activity_agent.domain.models import Scene, UserRequest
from activity_agent.modules.theme_planner import ThemePlanner, FRIENDS_THEMES, COUPLE_THEMES, HANGZHOU_CITY_THEMES
from activity_agent.modules.dialogue_manager import DialogueManager


@dataclass
class ImprovementChecklist:
    """改进检查清单"""
    scenario: str
    user_input: str
    expected_scene: Scene
    expected_theme: str
    expected_stage: str | None = None
    notes: str = ""


class ThemeImprovementHelper:
    """主题辨别代码改进辅助工具"""

    def __init__(self, use_llm: bool = False) -> None:
        self.use_llm = use_llm
        if use_llm:
            self.agent = ActivityPlanningAgent.from_env()
        else:
            self.agent = ActivityPlanningAgent()
        self.theme_planner = ThemePlanner()
        self.dialogue_manager = DialogueManager()

    def analyze_single_input(self, user_input: str, scene_hint: Scene | None = None) -> dict[str, Any]:
        """
        分析单个用户输入的主题识别全过程

        返回: 包含每一步详细信息的字典
        """
        result = {
            "user_input": user_input,
            "scene_hint": str(scene_hint) if scene_hint else None,
            "steps": {}
        }

        # Step 1: 理解用户输入
        try:
            understanding = self.dialogue_manager._understand(user_input, scene_hint=scene_hint)
            result["steps"]["understanding"] = {
                "scene": str(understanding.scene) if understanding.scene else None,
                "relationship_stage": understanding.relationship_stage,
                "relationship_goal": understanding.relationship_goal,
                "mood_tags": understanding.mood_tags,
                "confidence": understanding.confidence,
            }
        except Exception as e:
            result["steps"]["understanding"] = {"error": str(e)}

        # Step 2: 构建 UserRequest 并获取主题
        try:
            mock_request = self._build_mock_request(user_input, scene_hint)
            result["steps"]["request"] = {
                "scene": str(mock_request.scene),
                "mood_tags": mock_request.mood_tags,
                "experience_tags": mock_request.experience_tags,
                "relationship_stage": mock_request.relationship_stage,
            }

            # Step 3: 主题规划
            themes = self.theme_planner.plan(mock_request)
            result["steps"]["themes"] = [
                {"id": theme.id, "name": theme.name}
                for theme in themes
            ]

            # Step 4: 详细评分分析
            result["steps"]["scoring"] = self._analyze_scoring(mock_request)

        except Exception as e:
            result["steps"]["planning"] = {"error": str(e)}

        return result

    def _build_mock_request(self, text: str, scene_hint: Scene | None) -> UserRequest:
        """构建模拟请求"""
        understanding = self.dialogue_manager._understand(text, scene_hint=scene_hint)
        return UserRequest(
            user_id="test",
            session_id="test",
            scene=understanding.scene or (scene_hint or Scene.FRIENDS),
            mood_tags=understanding.mood_tags,
            experience_tags=[],
            relationship_stage=understanding.relationship_stage,
            relationship_goal=understanding.relationship_goal,
            hard_constraints=understanding.constraints,
            journey_duration=None,
            weather_sensitive=False,
            location_anchor="",
        )

    def _analyze_scoring(self, request: UserRequest) -> dict[str, Any]:
        """详细分析主题评分过程"""
        analysis = {}

        # 朋友主题评分
        analysis["friends"] = []
        for theme in FRIENDS_THEMES:
            score = self.theme_planner._score_friends(theme, request)
            analysis["friends"].append({
                "theme_id": theme.id,
                "theme_name": theme.name,
                "score": score,
                "trigger_tags": theme.trigger_tags,
            })

        # 情侣主题评分
        analysis["couple"] = []
        for theme in COUPLE_THEMES:
            score = self.theme_planner._score_couple(theme, request)
            analysis["couple"].append({
                "theme_id": theme.id,
                "theme_name": theme.name,
                "score": score,
                "stages": theme.stages,
                "goals": theme.goals,
            })

        # 杭州主题评分
        analysis["hangzhou"] = []
        is_hangzhou = self.theme_planner._is_hangzhou_day_out(request)
        analysis["is_hangzhou_day_out"] = is_hangzhou
        if is_hangzhou:
            for theme in HANGZHOU_CITY_THEMES:
                score = self.theme_planner._score_hangzhou(theme, request)
                analysis["hangzhou"].append({
                    "theme_id": theme.id,
                    "theme_name": theme.name,
                    "score": score,
                    "trigger_tags": theme.trigger_tags,
                    "experience_tags": theme.experience_tags,
                })

        return analysis

    def print_analysis_report(self, user_input: str, scene_hint: Scene | None = None) -> None:
        """打印美观的分析报告"""
        result = self.analyze_single_input(user_input, scene_hint)

        print("=" * 80)
        print("主题辨别分析报告")
        print("=" * 80)
        print(f"用户输入: {result['user_input']}")
        print(f"场景提示: {result['scene_hint']}")
        print()

        if "understanding" in result["steps"]:
            print("1. 用户需求理解")
            print("-" * 80)
            under = result["steps"]["understanding"]
            if "error" in under:
                print(f"❌ 错误: {under['error']}")
            else:
                print(f"场景识别: {under['scene']}")
                print(f"关系阶段: {under['relationship_stage']}")
                print(f"关系目标: {under['relationship_goal']}")
                print(f"情绪标签: {under['mood_tags']}")
                print(f"置信度: {under['confidence']:.2f}")
            print()

        if "themes" in result["steps"]:
            print("2. 推荐主题列表")
            print("-" * 80)
            for i, theme in enumerate(result["steps"]["themes"], 1):
                print(f" {i}. {theme['name']} ({theme['id']})")
            print()

        if "scoring" in result["steps"]:
            print("3. 详细评分分析")
            print("-" * 80)
            scoring = result["steps"]["scoring"]
            print(f"是否杭州主题: {'是' if scoring['is_hangzhou_day_out'] else '否'}")
            print()

            print("朋友主题评分:")
            for item in sorted(scoring["friends"], key=lambda x: x["score"], reverse=True):
                print(f"  {item['theme_name']} (score: {item['score']})")
                print(f"    触发标签: {item['trigger_tags']}")
            print()

            print("情侣主题评分:")
            for item in sorted(scoring["couple"], key=lambda x: x["score"], reverse=True):
                print(f"  {item['theme_name']} (score: {item['score']})")
                print(f"    适用阶段: {item['stages']}")
                print(f"    适用目标: {item['goals']}")
            print()

            if scoring["hangzhou"]:
                print("杭州主题评分:")
                for item in sorted(scoring["hangzhou"], key=lambda x: x["score"], reverse=True):
                    print(f"  {item['theme_name']} (score: {item['score']})")
                    print(f"    触发标签: {item['trigger_tags']}")
                    print(f"    体验标签: {item['experience_tags']}")
                print()

        print("=" * 80)

    def test_improvement_checklist(self, checklist: list[ImprovementChecklist]) -> list[dict[str, Any]]:
        """测试改进检查清单"""
        results = []

        for item in checklist:
            print(f"测试: {item.scenario}")
            result = self.analyze_single_input(item.user_input, item.expected_scene)

            passed = True
            actual_theme = None

            if "themes" in result["steps"] and result["steps"]["themes"]:
                actual_theme = result["steps"]["themes"][0]["id"]
                if actual_theme != item.expected_theme:
                    passed = False

            test_result = {
                "scenario": item.scenario,
                "user_input": item.user_input,
                "expected_theme": item.expected_theme,
                "actual_theme": actual_theme,
                "passed": passed,
                "notes": item.notes,
            }
            results.append(test_result)

            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} - 期望: {item.expected_theme}, 实际: {actual_theme}")
            print()

        # 统计
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        print(f"总计: {total} 个测试, 通过: {passed} 个, 失败: {total - passed} 个")

        return results


def main():
    """示例：使用改进辅助工具"""
    print("主题辨别代码改进辅助工具")
    print()

    helper = ThemeImprovementHelper(use_llm=False)

    # 测试示例 1
    print("测试示例 1: 朋友疯玩")
    helper.print_analysis_report("想好好疯一下，解压", Scene.FRIENDS)
    print()

    # 测试示例 2
    print("测试示例 2: 情侣约会")
    helper.print_analysis_report("第一次约会，怕尴尬", Scene.COUPLE)
    print()

    # 测试检查清单
    print("运行检查清单...")
    checklist = [
        ImprovementChecklist(
            scenario="朋友疯玩解压",
            user_input="想好好疯一下，解压",
            expected_scene=Scene.FRIENDS,
            expected_theme="friends_release",
            notes="测试发疯解压局识别",
        ),
        ImprovementChecklist(
            scenario="情侣初次约会",
            user_input="第一次约她，怕尴尬",
            expected_scene=Scene.COUPLE,
            expected_theme="couple_warmup",
            expected_stage="暧昧/追求中",
            notes="测试情侣轻升温约会识别",
        ),
        ImprovementChecklist(
            scenario="杭州西湖游",
            user_input="去杭州西湖逛逛",
            expected_scene=Scene.FRIENDS,
            expected_theme="hz_westlake_easy",
            notes="测试杭州主题识别",
        ),
    ]

    helper.test_improvement_checklist(checklist)


if __name__ == "__main__":
    main()
