# 主题确认功能验证 - 使用文档

## 1. 概述

本验证工具用于自动测试系统通过多轮对话与用户确认主题、关系阶段、预算、时间等关键信息的能力。它从 `activity_agent/data/theme_keyword_seeds.py` 读取参考主题定义，模拟多轮对话流程，记录每一轮交互，并自动生成通过率统计与异常汇总报告。

## 2. 测试环境准备

### 2.1 系统要求

- Python >= 3.11
- 项目根目录已配置完成（可直接运行 `python demo.py`）
- 无需额外第三方依赖（仅使用 Python 标准库 + 项目现有代码）

### 2.2 目录结构

```
meituan2/
├── tests/
│   ├── theme_confirmation_harness.py      # 测试框架核心：执行器、报告生成器
│   ├── theme_confirmation_cases.py        # 默认用例集
│   ├── run_theme_confirmation_validation.py  # 快速入口
│   └── test_theme_confirmation_validation.py  # unittest 集成入口
├── reports/
│   ├── theme_confirmation_report.md       # Markdown 报告
│   └── theme_confirmation_report.json     # JSON 结构化报告
├── activity_agent/data/
│   └── theme_keyword_seeds.py             # 主题参考定义（必选）
└── docs/
    └── theme_confirmation_validation_guide.md  # 本文档
```

## 3. 快速开始

### 3.1 运行完整验证套件

从项目根目录执行以下任一命令：

#### 方式 1：使用快速入口（推荐）
```bash
python -m tests.run_theme_confirmation_validation
```

#### 方式 2：使用 unittest
```bash
python -m unittest tests.test_theme_confirmation_validation
```

运行完成后，会在 `reports/` 目录下生成两份报告：
- `theme_confirmation_report.md`：人类可读的详细报告
- `theme_confirmation_report.json`：结构化报告，便于后续解析与二次开发

### 3.2 运行最小示例

如果你想先看一个简单的测试如何工作，可以直接在 Python 交互式 shell 中运行：

```python
from tests.theme_confirmation_harness import ThemeConfirmationHarness
from tests.theme_confirmation_cases import build_theme_confirmation_cases

harness = ThemeConfirmationHarness()
suite = harness.run_cases(build_theme_confirmation_cases())

print(f"总用例数: {suite.metrics.total_cases}")
print(f"通过数: {suite.metrics.passed_cases}")
print(f"主题准确率: {suite.metrics.theme_accuracy:.2%}")

# 保存报告
suite.save_markdown_report("reports/minimal_report.md")
```

## 4. 报告解读

### 4.1 报告头部

报告头部包含以下关键信息：

| 字段 | 说明 |
|------|------|
| 生成时间 | 报告生成的 ISO 时间戳 |
| 主题参考定义文件 | 测试时使用的主题来源 |
| 测试用例总数 | 本次运行的用例总数 |
| 通过用例数 | 校验通过的用例数 |
| 用例通过率 | 通过用例数 / 总用例数 |
| 主题定位准确率 | 最终返回的主题与预期一致的用例比例 |
| 关系阶段定位准确率 | 仅适用于情侣场景，关系阶段与预期一致的比例 |
| 异常用例数 | 发生超时、格式错误、流程中断的用例数 |
| 平均对话轮数 | 所有用例的平均对话轮次 |

### 4.2 执行结果总览

表格列说明：

| 列 | 说明 |
|----|------|
| 用例ID | 唯一标识，如 TC-01 |
| 分类 | 信息明确/信息模糊/歧义信息/边界场景 |
| 结果 | PASS / FAIL |
| 最终主题 | 系统返回的首个主题选项 |
| 关系阶段 | 仅适用于情侣场景 |
| 状态 | 对话结束时的系统状态（如 awaiting_selection） |
| 异常 | 若有异常，显示异常类型 |

### 4.3 单条用例详情

每条用例包含：
- **分类与描述**：测试场景说明
- **主题参考依据**：从 `theme_keyword_seeds.py` 中匹配到的预期主题定义
- **最终定位**：scene / relationship_stage / top_theme
- **校验明细**：逐项展示哪些校验通过/失败
- **对话转录**：完整的用户输入与系统输出轮次，包含状态与 next_step

### 4.4 问题汇总

所有失败/异常用例的快速索引，便于定位高频问题。

## 5. 测试用例设计思路

### 5.1 场景覆盖策略

| 分类 | 典型用例 | 设计目标 |
|------|----------|----------|
| 信息明确 | 用户直接给出所有关键信息 | 验证系统在高置信度输入下直接定位主题的能力 |
| 信息模糊 | 开场模糊，需要多轮追问 | 验证系统引导用户补充信息的流程 |
| 歧义信息 | 输入存在多义可能 | 验证系统的降歧/追问策略 |
| 边界场景 | 特殊关系阶段（修复、纪念日）、极端预算/时间 | 验证边界情况下的处理 |
| 异常机制 | 超时、响应错误、格式错误 | 验证系统的鲁棒性与错误记录能力 |

### 5.2 主题匹配规则

主题匹配参考 `activity_agent/data/theme_keyword_seeds.py` 中的定义：
- 如果主题名称或主题 ID 出现在预期列表中，则认为主题匹配
- 情侣场景额外校验 `relationship_stage` 和 `relationship_goal`
- 同时检查最终状态是否为 `awaiting_selection`（表示已给出选项）

### 5.3 状态迁移验证

工具会检查对话过程中的状态：
- 场景不明确 → `identifying_scene`
- 朋友场景 → `collecting_friends_context`
- 情侣场景 → `collecting_couple_context`
- 信息完整 → `ready_to_plan` → `awaiting_selection`

## 6. 自定义测试用例

### 6.1 用例结构

一个测试用例是 `ThemeConfirmationCase` 类型的对象，包含：
```python
@dataclass
class ThemeConfirmationCase:
    case_id: str                             # 用例唯一ID，如 "TC-99"
    title: str                               # 用例标题
    category: str                            # 分类：信息明确/模糊/歧义/边界
    description: str                         # 详细描述
    turns: list[ThemeConfirmationTurn]      # 对话轮次序列
    expected_scene: Scene                    # 预期场景：FRIENDS/COUPLE
    expected_relationship_stage: str | None = None  # 情侣场景：关系阶段
    expected_relationship_goal: str | None = None   # 情侣场景：关系目标
    expected_theme_ids_or_names: list[str] | None = None  # 预期主题列表
    expected_final_state: str | None = None # 预期最终状态，如 "awaiting_selection"
    require_options: bool = True             # 是否要求最终给出选项
    min_options: int = 3                     # 最小选项数
```

### 6.2 对话轮次结构

每一轮是 `ThemeConfirmationTurn` 类型：
```python
@dataclass
class ThemeConfirmationTurn:
    message: str                             # 用户说的话
    scene_hint: Scene | str | None = None    # 可选：显式场景提示
```

### 6.3 添加自定义用例

创建 `tests/my_custom_cases.py`：

```python
from __future__ import annotations
from activity_agent.domain import Scene
from tests.theme_confirmation_harness import ThemeConfirmationCase, ThemeConfirmationTurn

def build_my_custom_cases():
    return [
        ThemeConfirmationCase(
            case_id="MY-01",
            title="我的第一个自定义用例",
            category="信息明确",
            description="用户一句话给出完整信息。",
            turns=[
                ThemeConfirmationTurn("想和女朋友约会，人均300，周末下午"),
                ThemeConfirmationTurn("默认"),
            ],
            expected_scene=Scene.COUPLE,
            expected_relationship_stage="稳定情侣",
            expected_theme_ids_or_names=["轻升温不尴尬约会", "把普通周末过成小纪念日"],
            expected_final_state="awaiting_selection",
            require_options=True,
            min_options=2,
        ),
        # 继续添加更多用例...
    ]
```

然后在 `tests/run_theme_confirmation_validation.py` 或你自己的入口中使用：

```python
from tests.theme_confirmation_harness import ThemeConfirmationHarness
from tests.my_custom_cases import build_my_custom_cases

harness = ThemeConfirmationHarness()
suite = harness.run_cases(build_my_custom_cases())
suite.save_markdown_report("reports/my_custom_report.md")
```

## 7. 异常捕获机制

工具内置以下异常捕获与记录：
- **超时**：单轮对话超过 `timeout_seconds`（默认 10 秒）
- **流程中断**：执行对话时发生未捕获异常
- **格式错误**：返回的响应缺失必要字段（如 message 为空、无状态）

所有异常会被记录在报告中，包含堆栈信息，便于定位问题。

## 8. 常见问题

### 8.1 为什么主题识别准确率低？

当前测试套件中的朋友/情侣主题（如“下班回血局”）在系统现有实现中，当用户提到“杭州”时会优先使用杭州城市主题（如“杭州老城烟火半日局”）。这是预期的业务行为，你可以：
1. 调整预期主题列表为杭州主题
2. 或在测试用例中明确不引入“杭州”相关信息，只测试朋友/情侣专属主题

### 8.2 如何只测试部分用例？

在 `build_theme_confirmation_cases()` 中根据需要筛选：

```python
all_cases = build_theme_confirmation_cases()
selected_cases = [c for c in all_cases if c.category == "信息明确"]
```

### 8.3 可以用真实 LLM 测试吗？

是的。工具默认使用项目配置的 `ActivityPlanningAgent`，如果 `.env` 中配置了真实 LLM，它会直接使用。如果要强制使用规则模式或 Mock 模式，请在初始化 agent 时传入对应参数。

## 9. 下一步

当你完成测试后：
1. 查看报告中的问题汇总，定位高频失败点
2. 根据需要修改业务逻辑或调整预期
3. 添加新的自定义用例覆盖更多场景
4. 将测试集成到你的 CI/CD 流程中
