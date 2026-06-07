from __future__ import annotations

from pathlib import Path

from tests.acceptance_matrix.acceptance_validation_cases import build_acceptance_cases
from tests.acceptance_matrix.acceptance_validation_harness import (
    DEFAULT_REPORT_DIR,
    AcceptanceValidationHarness,
)


def main() -> int:
    harness = AcceptanceValidationHarness()
    suite = harness.run_cases(build_acceptance_cases(), output_dir=Path(DEFAULT_REPORT_DIR))

    print("Acceptance matrix validation completed.")
    print(f"Cases: {suite.metrics.total_cases}")
    print(f"Passed: {suite.metrics.passed_cases}")
    print(f"Failed: {suite.metrics.failed_cases}")
    print(f"Case pass rate: {suite.metrics.case_pass_rate:.2%}")
    print(f"Validation pass rate: {suite.metrics.validation_pass_rate:.2%}")
    print(f"Markdown report: {suite.markdown_report_path}")
    print(f"JSON report: {suite.json_report_path}")
    return 0 if suite.metrics.failed_cases == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
