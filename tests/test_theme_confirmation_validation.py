from __future__ import annotations

import time
import unittest

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import AgentResponse, Intent, Scene

from tests.theme_confirmation_cases import build_theme_confirmation_cases
from tests.theme_confirmation_harness import ThemeConfirmationCase, ThemeConfirmationHarness, ThemeConfirmationTurn


class ThemeConfirmationValidationTest(unittest.TestCase):
    def test_default_suite_runs_without_fatal_errors(self) -> None:
        harness = ThemeConfirmationHarness()
        suite = harness.run_cases(build_theme_confirmation_cases())

        self.assertEqual(suite.metrics.total_cases, 10)
        # 仅验证框架可执行，报告可生成，不强制要求业务准确率
        self.assertEqual(suite.metrics.exception_case_count, 0)

    def test_timeout_is_captured_in_case_result(self) -> None:
        def slow_turn_executor(agent: ActivityPlanningAgent, session_id: str, turn: ThemeConfirmationTurn) -> AgentResponse:
            time.sleep(0.2)
            return agent.chat_with_guidance(session_id, turn.message, scene_hint=turn.scene_hint)

        harness = ThemeConfirmationHarness(timeout_seconds=0.01, turn_executor=slow_turn_executor)
        case = ThemeConfirmationCase(
            case_id="ERR-01",
            title="超时捕获",
            category="异常机制",
            description="通过一个故意变慢的执行器验证超时处理。",
            turns=[ThemeConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS)],
            expected_scene=Scene.FRIENDS,
            require_options=False,
            expected_final_state="collecting_friends_context",
        )

        result = harness.run_case(case)

        self.assertFalse(result.passed)
        self.assertEqual(result.exception_type, "DialogueTurnTimeoutError")

    def test_runtime_exception_is_captured_in_case_result(self) -> None:
        def broken_turn_executor(agent: ActivityPlanningAgent, session_id: str, turn: ThemeConfirmationTurn) -> AgentResponse:
            raise RuntimeError("simulated dialogue crash")

        harness = ThemeConfirmationHarness(turn_executor=broken_turn_executor)
        case = ThemeConfirmationCase(
            case_id="ERR-02",
            title="流程中断捕获",
            category="异常机制",
            description="通过一个显式抛错的执行器验证流程中断记录。",
            turns=[ThemeConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS)],
            expected_scene=Scene.FRIENDS,
            require_options=False,
            expected_final_state="collecting_friends_context",
        )

        result = harness.run_case(case)

        self.assertFalse(result.passed)
        self.assertEqual(result.exception_type, "RuntimeError")
        self.assertIn("simulated dialogue crash", result.exception_message or "")

    def test_invalid_response_format_is_captured_in_case_result(self) -> None:
        def invalid_turn_executor(agent: ActivityPlanningAgent, session_id: str, turn: ThemeConfirmationTurn) -> AgentResponse:
            return AgentResponse(
                session_id=session_id,
                intent=Intent.PLAN,
                scene=Scene.FRIENDS,
                message=" ",
            )

        harness = ThemeConfirmationHarness(turn_executor=invalid_turn_executor)
        case = ThemeConfirmationCase(
            case_id="ERR-03",
            title="输出格式错误捕获",
            category="异常机制",
            description="通过一个非法响应对象验证格式校验逻辑。",
            turns=[ThemeConfirmationTurn("朋友局", scene_hint=Scene.FRIENDS)],
            expected_scene=Scene.FRIENDS,
            require_options=False,
            expected_final_state="collecting_friends_context",
        )

        result = harness.run_case(case)

        self.assertFalse(result.passed)
        self.assertEqual(result.exception_type, "ResponseFormatError")


if __name__ == "__main__":
    unittest.main()
