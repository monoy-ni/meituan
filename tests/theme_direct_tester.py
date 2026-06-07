from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Any

from activity_agent import ActivityPlanningAgent
from activity_agent.domain.models import Scene, UserRequest
from activity_agent.modules.theme_planner import ThemePlanner, FRIENDS_THEMES, COUPLE_THEMES, HANGZHOU_CITY_THEMES


@dataclass
class ThemeTestResult:
    case_id: str
    title: str
    input_text: str
    expected_theme_id: str | None
    actual_theme_id: str | None
    expected_scene: Scene | None
    actual_scene: Scene | None
    success: bool
    message: str
    all_theme_scores: dict[str, int]


class ThemeDirectTester:
    """直接测试主题选择功能 - 不通过多轮对话流程"""

    def __init__(self):
        self.agent = ActivityPlanningAgent()
        self.theme_planner = ThemePlanner()

    def _get_theme_name_by_id(self, theme_id: str) -> str:
        all_themes = FRIENDS_THEMES + COUPLE_THEMES + HANGZHOU_CITY_THEMES
        for theme in all_themes:
            if theme.id == theme_id:
                return theme.name
        return theme_id

    def test_single_input(self, case_id: str, title: str, input_text: str, 
                        expected_theme_id: str | None = None, 
                        expected_scene: Scene | None = None) -> ThemeTestResult:
        """测试单个用户输入"""
        
        try:
            # 1. 使用 intent_router 和 context_collector 分析
            route = self.agent.intent_router.route(input_text, scene_hint=expected_scene)
            request, missing_questions, assumptions = self.agent.context_collector.collect(route, input_text)
            
            # 2. 使用 ThemePlanner 选择主题
            themes = self.theme_planner.plan(request)
            actual_theme_id = themes[0].id if themes else None
            
            # 3. 获取评分详情
            all_scores = self._get_all_scores(request)
            
            # 4. 验证结果
            actual_scene = request.scene
            theme_match = (expected_theme_id is None) or (actual_theme_id == expected_theme_id)
            scene_match = (expected_scene is None) or (actual_scene == expected_scene)
            success = theme_match and scene_match
            
            message = (
                f"PASS" if success else 
                f"FAIL - Expected theme: {self._get_theme_name_by_id(expected_theme_id)}, "
                f"Actual: {self._get_theme_name_by_id(actual_theme_id)}"
            )

            return ThemeTestResult(
                case_id=case_id,
                title=title,
                input_text=input_text,
                expected_theme_id=expected_theme_id,
                actual_theme_id=actual_theme_id,
                expected_scene=expected_scene,
                actual_scene=actual_scene,
                success=success,
                message=message,
                all_theme_scores=all_scores
            )
        except Exception as e:
            return ThemeTestResult(
                case_id=case_id,
                title=title,
                input_text=input_text,
                expected_theme_id=expected_theme_id,
                actual_theme_id=None,
                expected_scene=expected_scene,
                actual_scene=None,
                success=False,
                message=f"❌ ERROR: {str(e)}",
                all_theme_scores={}
            )

    def _get_all_scores(self, request: UserRequest) -> dict[str, int]:
        """获取所有主题的评分"""
        scores = {}
        
        is_hangzhou = self.theme_planner._is_hangzhou_day_out(request)
        if is_hangzhou:
            for theme in HANGZHOU_CITY_THEMES:
                scores[theme.id] = self.theme_planner._score_hangzhou(theme, request)
        else:
            if request.scene == Scene.COUPLE:
                for theme in COUPLE_THEMES:
                    scores[theme.id] = self.theme_planner._score_couple(theme, request)
            else:
                for theme in FRIENDS_THEMES:
                    scores[theme.id] = self.theme_planner._score_friends(theme, request)
        
        # 按分数排序
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def run_direct_tests():
    """运行直接主题测试"""

    print("=" * 80)
    print("Theme Selection Direct Test")
    print("=" * 80)

    tester = ThemeDirectTester()

    test_cases = [
        # 朋友局测试
        {
            "case_id": "TC_F_001",
            "title": "朋友回血局",
            "input_text": "和朋友下班，想放松一下，去个热闹点的地方",
            "expected_theme_id": "friends_recovery",
            "expected_scene": Scene.FRIENDS
        },
        {
            "case_id": "TC_F_002",
            "title": "发疯解压局",
            "input_text": "最近压力很大，和朋友想找个地方疯玩一下，放松解压",
            "expected_theme_id": "friends_release",
            "expected_scene": Scene.FRIENDS
        },
        {
            "case_id": "TC_F_003",
            "title": "低成本快乐局",
            "input_text": "和朋友一起玩，预算不高，人均100左右，开心就好",
            "expected_theme_id": "friends_budget",
            "expected_scene": Scene.FRIENDS
        },
        {
            "case_id": "TC_F_004",
            "title": "出片聊天局",
            "input_text": "想和朋友找个地方拍拍照，聊聊天，放松一下",
            "expected_theme_id": "friends_photo_chat",
            "expected_scene": Scene.FRIENDS
        },

        # 情侣约会测试
        {
            "case_id": "TC_C_001",
            "title": "暧昧/追求中，怕尴尬",
            "input_text": "想约喜欢的人出来，第一次，怕尴尬，想安排点轻松的",
            "expected_theme_id": "couple_warmup",
            "expected_scene": Scene.COUPLE
        },
        {
            "case_id": "TC_C_002",
            "title": "纪念日",
            "input_text": "纪念日，想和女朋友安排点浪漫有仪式感的",
            "expected_theme_id": "couple_memory",
            "expected_scene": Scene.COUPLE
        },
        {
            "case_id": "TC_C_003",
            "title": "关系修复",
            "input_text": "最近和女朋友吵架了，想找个安静地方缓和一下",
            "expected_theme_id": "couple_repair",
            "expected_scene": Scene.COUPLE
        },

        # 杭州主题测试
        {
            "case_id": "TC_HZ_001",
            "title": "西湖轻松打卡",
            "input_text": "和朋友在杭州，想去西湖看看，不想太累",
            "expected_theme_id": "hz_westlake_easy",
            "expected_scene": Scene.FRIENDS
        },
        {
            "case_id": "TC_HZ_002",
            "title": "老城烟火半日",
            "input_text": "杭州本地，想感受下老城烟火，吃点特色小吃",
            "expected_theme_id": "hz_old_town_fireworks",
            "expected_scene": Scene.FRIENDS
        },
        {
            "case_id": "TC_HZ_003",
            "title": "雨天室内低耗",
            "input_text": "今天杭州下雨，想找个室内的地方，不用太折腾",
            "expected_theme_id": "hz_rainy_indoor",
            "expected_scene": Scene.FRIENDS
        }
    ]

    results = []
    for case in test_cases:
        print(f"\n--- [{case['case_id']}] {case['title']} ---")
        print(f"Input: {case['input_text']}")
        result = tester.test_single_input(**case)
        results.append(result)
        print(f"Result: {result.message}")
        
        # 显示评分详情
        if result.all_theme_scores:
            print("Score details:")
            for theme_id, score in list(result.all_theme_scores.items())[:5]:
                print(f"  - {tester._get_theme_name_by_id(theme_id)}: {score}")

    # 汇总结果
    total = len(results)
    passed = sum(1 for r in results if r.success)
    
    print("\n" + "=" * 80)
    print(f"Test Summary: {passed}/{total} passed ({100.0 * passed / total:.1f}%)")
    print("=" * 80)
    
    # 保存结果
    output_file = Path(__file__).parent.parent / "reports" / "theme_direct_test_results.md"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Theme Selection Direct Test Results\n\n")
        f.write(f"- Total cases: {total}\n")
        f.write(f"- Passed: {passed}\n")
        f.write(f"- Pass rate: {100.0 * passed / total:.1f}%\n\n")
        
        f.write("## Detailed Results\n\n")
        for result in results:
            status_text = "PASS" if result.success else "FAIL"
            f.write(f"### [{status_text}] [{result.case_id}] {result.title}\n\n")
            f.write(f"- Input: {result.input_text}\n")
            f.write(f"- Result: {result.message}\n")
            if result.all_theme_scores:
                f.write("- Score details:\n")
                for theme_id, score in list(result.all_theme_scores.items())[:5]:
                    f.write(f"  - {tester._get_theme_name_by_id(theme_id)}: {score}\n")
            f.write("\n")

    print(f"\nDetailed report saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    run_direct_tests()
