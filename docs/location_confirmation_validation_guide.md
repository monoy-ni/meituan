# 位置获取与高德地图API集成验证 - 使用说明

## 1. 概述

本验证工具用于自动化测试系统通过多轮对话获取用户位置信息、使用默认位置、以及通过高德地图API解析地理位置的完整流程。核心功能包括：

- 模拟真实对话流程，验证位置信息提取
- 测试默认位置（奥映世纪轩）的正确使用
- 验证高德地图API集成（地址解析、坐标获取）
- 记录完整对话过程，生成详细测试报告
- 支持自定义测试用例扩展

## 2. 项目结构

```
meituan2/
├── tests/
│   ├── location_confirmation_harness.py      # 测试框架核心
│   ├── location_confirmation_cases.py        # 默认测试用例集
│   ├── run_location_confirmation_test.py      # 快速运行脚本
│   └── test_location_confirmation.py          # unittest集成测试
├── reports/                                    # 测试报告输出目录
│   ├── location_confirmation_report.md        # Markdown报告
│   └── location_confirmation_report.json      # JSON结构化报告
├── docs/
│   └── location_confirmation_validation_guide.md  # 本文档
└── .env.example                              # 环境变量配置示例
```

## 3. 环境配置

### 3.1 系统要求

- Python >= 3.11
- 项目根目录已配置完成
- 依赖库已安装

### 3.2 高德地图API配置

为了启用真实的高德地图API测试，需要在 `.env` 文件中配置以下变量：

```env
# 高德地图Web服务API Key
# 申请地址: https://console.amap.com/dev/key/app
AMAP_API_KEY=your_amap_api_key_here

# 高德地图城市编码（默认杭州: 330100）
AMAP_CITY=330100

# POI搜索关键词（可选）
AMAP_POI_KEYWORDS=美食,景点,博物馆,手作,茶馆,酒吧,桌游,密室

# 地图提供商
ACTIVITY_AGENT_MAP_PROVIDER=amap
```

**配置步骤：**

1. 复制 `.env.example` 为 `.env`
2. 登录高德开放平台（https://console.amap.com）
3. 创建应用并申请Web服务API Key
4. 将API Key填入 `AMAP_API_KEY`
5. 其他配置项可保持默认值

**注意：**
- 如果不配置 `AMAP_API_KEY`，系统将使用seed数据中的默认坐标
- 即使没有真实API Key，测试框架依然可以运行（验证位置解析逻辑）
- 默认位置硬编码为：奥映世纪轩，民祥路与平澜路交汇处(地铁6号线丰北站C出口)

### 3.3 默认位置定义

系统默认位置定义在 `activity_agent/domain/models.py` 的 `UserRequest` 类中：

```python
origin_name: str = "奥映世纪轩"
origin_address: str = "民祥路与平澜路交汇处(地铁6号线丰北站C出口)"
origin_amap_url: str = "https://surl.amap.com/4sRsg3c1oa7b"
origin_longitude: float | None = 120.2425
origin_latitude: float | None = 30.2426
```

## 4. 快速开始

### 4.1 方式一：使用快速运行脚本

从项目根目录执行：

```bash
python -m tests.run_location_confirmation_test
```

或者直接运行：

```bash
python tests/run_location_confirmation_test.py
```

### 4.2 方式二：使用 unittest

```bash
python -m unittest tests.test_location_confirmation
```

### 4.3 运行单个单元测试

```bash
python -m unittest tests.test_location_confirmation.LocationConfirmationTest.test_default_location_is_used_when_not_provided
```

## 5. 测试用例设计

### 5.1 已覆盖的测试场景

| 场景 | 用例数 | 说明 |
|------|--------|------|
| 用户明确给出位置 | 2 | 西湖、河坊街等明确位置 |
| 用户未给位置，使用默认值 | 1 | 验证奥映世纪轩默认值 |
| 位置信息在后续轮次补充 | 1 | 第三轮才给出位置 |
| 模糊位置描述 | 1 | 地铁6号线附近 |
| 包含完整地址 | 1 | 民祥路与平澜路交汇处 |
| 提及地铁出口 | 1 | 丰北站C出口 |
| 位置+搜索半径 | 1 | 武林广场+周边3公里 |
| 用户中途修正位置 | 1 | 西湖文化广场→武林广场 |
| 多场景位置一致性 | 1 | 情侣场景默认位置 |
| 复杂位置描述 | 1 | 多个地标结合 |
| 纯地址无场景提示 | 1 | 先给位置，再给场景 |
| 高德地图URL测试 | 1 | 验证默认URL |

### 5.2 测试用例定义结构

一个测试用例是 `LocationTestCase` 类型的对象：

```python
@dataclass
class LocationTestCase:
    case_id: str                              # 用例唯一标识
    title: str                                # 用例标题
    category: str                             # 分类（信息明确/默认值/信息补充等）
    description: str                          # 详细描述
    turns: list[LocationConfirmationTurn]     # 对话轮次
    expected_final_location: Optional[str]    # 预期位置名称
    expected_final_address: Optional[str]     # 预期详细地址
    expected_longitude: Optional[float]       # 预期经度
    expected_latitude: Optional[float]        # 预期纬度
    expected_amap_url: Optional[str]          # 预期高德URL
    expected_uses_default: bool = False       # 是否使用默认位置
    expected_final_state: str = "awaiting_selection"  # 预期最终状态
    require_options: bool = True              # 是否要求生成选项
    min_options: int = 3                      # 最小选项数
```

每个对话轮次：

```python
@dataclass
class LocationConfirmationTurn:
    user_message: str                         # 用户说的话
    scene_hint: Optional[Scene | str] = None # 可选场景提示
    delay_seconds: float = 0.0               # 延迟秒数
```

## 6. 自定义测试用例

### 6.1 添加自定义用例

创建 `tests/my_location_cases.py`：

```python
from __future__ import annotations

from activity_agent.domain import Scene
from tests.location_confirmation_harness import (
    LocationTestCase,
    LocationConfirmationTurn,
    DEFAULT_LOCATION,
)


def build_my_custom_cases() -> list[LocationTestCase]:
    return [
        # 你的自定义用例
        LocationTestCase(
            case_id="MY-01",
            title="我的自定义测试",
            category="自定义",
            description="测试我公司附近的位置",
            turns=[
                LocationConfirmationTurn("朋友局，从我公司楼下出发", scene_hint=Scene.FRIENDS),
                LocationConfirmationTurn("人均200，想吃饭"),
                LocationConfirmationTurn("今晚"),
                LocationConfirmationTurn("默认"),
            ],
            expected_final_state="awaiting_selection",
            require_options=True,
        ),
    ]
```

### 6.2 运行自定义用例

创建 `tests/run_my_location_test.py`：

```python
from __future__ import annotations

from tests.location_confirmation_harness import LocationConfirmationHarness
from tests.my_location_cases import build_my_custom_cases


def main():
    harness = LocationConfirmationHarness()
    cases = build_my_custom_cases()
    suite = harness.run_cases(cases)
    
    harness.save_markdown_report(suite, "reports/my_location_report.md")
    harness.save_json_report(suite, "reports/my_location_report.json")
    
    print(f"完成！通过率: {suite.metrics.case_pass_rate:.2%}")


if __name__ == "__main__":
    main()
```

## 7. 测试报告解读

### 7.1 Markdown报告

Markdown报告包含以下部分：

1. **统计摘要**
   - 总用例数、通过数、失败数、异常数
   - 用例通过率、位置名称准确率、地址准确率、坐标准确率
   - 默认位置使用次数、高德API调用次数
   - 平均对话轮数

2. **执行结果总览表格**
   - 用例ID、分类、结果
   - 最终位置、地址
   - 对话状态、异常信息

3. **问题汇总**
   - 列出所有失败用例的失败原因

4. **用例详情**
   - 每个用例的完整对话记录
   - 每轮对话的状态和位置解析结果
   - 最终位置信息（名称、地址、经纬度、URL）

### 7.2 JSON报告

JSON报告包含完整的结构化数据，便于后续分析：

```json
{
  "generated_at": "2026-06-07T17:30:00",
  "amap_configured": true,
  "metrics": {...},
  "cases": [
    {
      "case_id": "LOC-01",
      "title": "...",
      "passed": true,
      "execution_time_ms": 1234.5,
      "final_request": {...},
      "turns": [...]
    }
  ]
}
```

### 7.3 常见问题排查

| 问题 | 可能原因 | 排查方法 |
|------|----------|----------|
| 位置总是默认值 | AMAP_API_KEY未配置 | 检查.env文件 |
| 高德API调用失败 | API Key无效或过期 | 登录高德控制台检查 |
| 测试用例通过率低 | 位置解析逻辑问题 | 查看对话记录，定位问题轮次 |
| 测试超时 | 单轮对话执行过久 | 检查是否有网络请求卡住 |
| 坐标总是默认值 | 地址解析失败 | 检查AMAP API返回 |

## 8. 核心代码链路

### 8.1 位置解析流程

用户输入 → `DialogueManager._understand()` → `ContextCollector.collect()` → `UserRequest` → `_resolve_origin_with_amap()` → 最终位置

### 8.2 关键文件位置

| 文件 | 功能 |
|------|------|
| `activity_agent/domain/models.py` | `UserRequest` 类定义默认位置 |
| `activity_agent/modules/dialogue_manager.py` | 对话状态管理，位置提取 |
| `activity_agent/modules/context_collector.py` | 上下文收集，位置解析 |
| `activity_agent/providers/live_sources.py` | `AmapWebServiceClient` 高德API客户端 |
| `activity_agent/agent.py` | `_resolve_origin_with_amap()` 位置解析方法 |

## 9. 常见问题

### 9.1 没有高德API Key可以测试吗？

可以。测试框架会正常运行，位置解析会使用内置的默认坐标或规则匹配，不会调用真实API。

### 9.2 如何调试位置解析问题？

1. 运行测试并查看Markdown报告中的对话记录
2. 检查每轮对话的 `location_parsed` 字段
3. 在代码中打断点调试 `ContextCollector._parse_location()` 方法

### 9.3 测试框架会修改数据库吗？

不会。测试使用独立的会话（session），不会影响现有数据。

### 9.4 可以测试真实API吗？

可以。配置好 `AMAP_API_KEY` 后，系统会调用真实的高德地图API进行地址解析。

## 10. 下一步

- 根据测试结果修复位置解析逻辑
- 添加更多测试用例覆盖边界场景
- 将位置验证集成到CI/CD流程
