import unittest

from tests.acceptance_matrix.acceptance_validation_cases import build_acceptance_cases
from tests.acceptance_matrix.acceptance_validation_harness import AcceptanceValidationHarness


class AcceptanceMatrixValidationTest(unittest.TestCase):
    def test_default_acceptance_cases_pass_with_diagnostics_available(self) -> None:
        suite = AcceptanceValidationHarness().run_cases(build_acceptance_cases())
        failures = [
            {
                "case_id": result.case_id,
                "title": result.title,
                "failed_validations": [
                    {
                        "name": validation.name,
                        "expected": validation.expected,
                        "actual": validation.actual,
                        "debug_hint": validation.debug_hint,
                    }
                    for validation in result.validations
                    if not validation.passed
                ],
                "exception": result.exception_type,
            }
            for result in suite.case_results
            if not result.passed
        ]

        self.assertEqual(suite.metrics.exception_cases, 0, failures)
        self.assertEqual(suite.metrics.failed_cases, 0, failures)


if __name__ == "__main__":
    unittest.main()
