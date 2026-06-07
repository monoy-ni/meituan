from __future__ import annotations

from pathlib import Path

from tests.theme_confirmation_cases import build_theme_confirmation_cases
from tests.theme_confirmation_harness import DEFAULT_REPORT_DIR, ThemeConfirmationHarness


def main() -> int:
    harness = ThemeConfirmationHarness()
    cases = build_theme_confirmation_cases()
    suite = harness.run_cases(cases, output_dir=Path(DEFAULT_REPORT_DIR))

    print("Theme confirmation validation completed.")
    print(f"Cases: {suite.metrics.total_cases}")
    print(f"Passed: {suite.metrics.passed_cases}")
    print(f"Failed: {suite.metrics.failed_cases}")
    print(f"Case pass rate: {suite.metrics.case_pass_rate:.2%}")
    print(f"Theme accuracy: {suite.metrics.theme_accuracy:.2%}")
    print(f"Relationship-stage accuracy: {suite.metrics.relationship_stage_accuracy:.2%}")
    print(f"Markdown report: {suite.markdown_report_path}")
    print(f"JSON report: {suite.json_report_path}")
    return 0 if suite.metrics.failed_cases == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
