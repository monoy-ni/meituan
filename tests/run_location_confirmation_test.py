#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        from tests.location_confirmation_harness import LocationConfirmationHarness
        from tests.location_confirmation_cases import build_location_test_cases
    except ImportError as e:
        print(f"Error importing test modules: {e}", file=sys.stderr)
        print("Please ensure you're running from the project root directory.", file=sys.stderr)
        return 1

    print("=" * 80)
    print("位置获取与高德地图API集成验证测试")
    print("=" * 80)
    print()

    harness = LocationConfirmationHarness()
    cases = build_location_test_cases()
    
    print(f"准备运行 {len(cases)} 个测试用例...")
    print()
    
    suite = harness.run_cases(cases)
    
    print("测试完成！")
    print()
    print("=" * 80)
    print("统计摘要")
    print("=" * 80)
    m = suite.metrics
    print(f"总用例数: {m.total_cases}")
    print(f"通过: {m.passed_cases}")
    print(f"失败: {m.failed_cases}")
    print(f"异常: {m.exception_cases}")
    print(f"用例通过率: {m.case_pass_rate:.2%}")
    print(f"位置名称准确率: {m.location_accuracy:.2%}")
    print(f"地址准确率: {m.address_accuracy:.2%}")
    print(f"坐标准确率: {m.coordinate_accuracy:.2%}")
    print(f"使用默认位置次数: {m.default_location_used_count}")
    print(f"高德地图API调用次数: {m.amap_api_called_count}")
    print(f"平均对话轮数: {m.avg_turns_per_case:.1f}")
    print()

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    markdown_path = reports_dir / "location_confirmation_report.md"
    json_path = reports_dir / "location_confirmation_report.json"
    
    harness.save_markdown_report(suite, str(markdown_path))
    harness.save_json_report(suite, str(json_path))
    
    print(f"Markdown报告已保存至: {markdown_path.absolute()}")
    print(f"JSON报告已保存至: {json_path.absolute()}")
    print()
    
    return 0 if m.exception_cases == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
