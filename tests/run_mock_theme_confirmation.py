from __future__ import annotations

from pathlib import Path

from tests.theme_confirmation_cases import build_theme_confirmation_cases
from tests.theme_confirmation_harness import DEFAULT_REPORT_DIR, ThemeConfirmationHarness


def main() -> int:
    """使用 Mock LLM 模式快速验证测试框架"""
    print("=" * 80)
    print("Theme Confirmation Validation Test - Mock Mode")
    print("=" * 80)
    
    # 临时修改使用 Mock 配置强制使用 Mock LLM
    # 这里通过修改环境变量来强制使用 Mock
    import os
    original_api_key = os.environ.get("ACTIVITY_AGENT_LLM_API_KEY")
    os.environ["ACTIVITY_AGENT_LLM_API_KEY"] = ""
    
    try:
        harness = ThemeConfirmationHarness()
        cases = build_theme_confirmation_cases()
        
        print(f"\n[INFO] Loaded {len(cases)} test cases")
        print(f"[INFO] Theme seed file: {harness.seed_reference.file_path}")
        print(f"[INFO] Theme catalog size: {len(harness.seed_reference.keywords_by_key)}")
        
        suite = harness.run_cases(cases, output_dir=Path(DEFAULT_REPORT_DIR))

        print("\n" + "=" * 80)
        print("Test Result Statistics")
        print("=" * 80)
        print(f"Total cases: {suite.metrics.total_cases}")
        print(f"Passed: {suite.metrics.passed_cases}")
        print(f"Failed: {suite.metrics.failed_cases}")
        print(f"Case pass rate: {suite.metrics.case_pass_rate:.2%}")
        print(f"Theme accuracy: {suite.metrics.theme_accuracy:.2%}")
        print(f"Relationship-stage accuracy: {suite.metrics.relationship_stage_accuracy:.2%}")
        print(f"Exception case count: {suite.metrics.exception_case_count}")
        print(f"Average turns per case: {suite.metrics.avg_turns_per_case:.1f}")
        print(f"\nMarkdown report: {suite.markdown_report_path}")
        print(f"JSON report: {suite.json_report_path}")
        print("=" * 80)
        
        return 0 if suite.metrics.failed_cases == 0 else 1
    finally:
        if original_api_key is not None:
            os.environ["ACTIVITY_AGENT_LLM_API_KEY"] = original_api_key


if __name__ == "__main__":
    raise SystemExit(main())
