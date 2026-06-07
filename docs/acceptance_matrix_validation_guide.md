# 8 项业务验收测试矩阵 - 使用文档

## 1. 概述

本验证工具用于集中验证当前产品的 8 个关键业务链路，并生成可定位问题的 Markdown / JSON 报告。

它不是简单的 “assert 通过/失败” 测试，而是会记录：

- 每个验收点的需求描述和关联源码
- 每个校验项的预期值、实际值、定位提示
- 多轮对话转录、`state`、`next_step`、最终请求快照
- mock 高德 / mock 美团 / LLM 商户组合器的调用记录
- 失败项的问题汇总和优先排查文件

## 2. 目录结构

```
meituan-agent/
├── tests/
│   └── acceptance_matrix/
│       ├── acceptance_validation_cases.py      # 8 个验收点的元数据
│       ├── acceptance_validation_harness.py    # 执行器、校验器、报告生成器
│       ├── run_acceptance_validation.py        # 推荐运行入口
│       ├── test_acceptance_validation.py       # unittest 集成入口
│       ├── scenario_01_theme_confirmation/
│       ├── scenario_02_location_amap_ip_default/
│       ├── scenario_03_distance_and_route_requirements/
│       ├── scenario_04_amap_poi_range_search/
│       ├── scenario_05_meituan_profiles_llm_selection/
│       ├── scenario_06_amap_route_planning/
│       ├── scenario_07_skill_experience_cards/
│       └── scenario_08_mock_booking_order/
├── reports/
│   ├── acceptance_matrix_report.md             # 人类可读诊断报告
│   └── acceptance_matrix_report.json           # 结构化诊断数据
└── docs/
    └── acceptance_matrix_validation_guide.md   # 本文档
```

## 3. 快速开始

### 3.1 运行完整诊断报告

从项目根目录执行：

```powershell
python -m tests.acceptance_matrix.run_acceptance_validation
```

运行完成后会生成：

- `reports/acceptance_matrix_report.md`
- `reports/acceptance_matrix_report.json`

### 3.2 使用 unittest 集成入口

如果只需要 CI 判断是否通过：

```powershell
python -m unittest tests.acceptance_matrix.test_acceptance_validation
```

如果要连同子目录里的单项验收测试一起跑：

```powershell
python -m unittest discover tests/acceptance_matrix
```

## 4. 报告解读

### 4.1 报告头部

| 字段 | 说明 |
| --- | --- |
| 测试项总数 | 8 个业务验收点 |
| 通过测试项 | 通过的验收点数量 |
| 测试项通过率 | 通过测试项 / 测试项总数 |
| 校验项总数 | 每个验收点下的细粒度字段校验总数 |
| 失败校验项 | 失败的字段/流程校验数量 |
| 校验项通过率 | 通过校验项 / 校验项总数 |
| 异常测试项 | 执行过程中发生异常的验收点数量 |

### 4.2 执行结果总览

总览表会列出：

- 验收 ID：`AC-01` 到 `AC-08`
- 分类：主题确认、位置确认、距离约束、POI 搜索、商户组合、路径规划、体验卡、预约下单
- 结果：PASS / FAIL
- 失败校验：失败时直接列出校验项名称
- 异常：如果运行中断，显示异常类型
- 主要关联文件：优先排查源码和测试文件

### 4.3 问题汇总

失败时优先看这里。每个失败校验会展示：

- 校验项名称
- 预期值
- 实际值
- 定位提示
- 关联文件

这部分就是为了避免只能看到一个断言失败，却不知道该查哪里。

### 4.4 单项详情

每个验收点会继续展开：

- 需求和描述
- 关联文件
- 校验明细
- 证据表
- 对话转录（适用于 AC-01、AC-03）
- 工具/外部接口调用记录（适用于高德、美团、LLM 相关链路）
- Traceback（如果发生异常）

## 5. 8 个验收点

| ID | 验收点 | 关键定位 |
| --- | --- | --- |
| AC-01 | AI 多轮交流确认主题 | `DialogueManager` 状态迁移、默认距离提示、最终出方案 |
| AC-02 | 集合位置、高德 IP 定位与默认位置 | `AmapWebServiceClient.ip_location()`、默认奥映世纪轩字段 |
| AC-03 | 距离要求与整体路径要求 | 搜索半径、路线公里数、路线分钟数写入 `UserRequest` 和 `route_plan` |
| AC-04 | 高德 POI 范围搜索 | `HybridLiveDataProvider.sync_theme_pois()`、around 搜索参数和 POI 入库 |
| AC-05 | mock 美团评价与 LLM 商户组合 | `merchant_profile()`、LLM prompt、编造商户过滤、主题 slots 组合 |
| AC-06 | 高德路径规划 | `walking_route()` 调用、route legs、总距离/时长、`within_limits` |
| AC-07 | 情侣/朋友 skill 体验卡 | `couple-date-designer`、`themed-outing-designer`、卡片完整字段 |
| AC-08 | mock 美团预约与下单 | 可用性检查、booking hold、AA draft、取消/确认订单边界 |

## 6. 添加或修改验收点

1. 修改 `tests/acceptance_matrix/acceptance_validation_cases.py` 中的验收点元数据。
2. 在 `tests/acceptance_matrix/acceptance_validation_harness.py` 中补对应执行逻辑和校验项。
3. 如果该验收点需要独立单项测试，在对应 `scenario_xx_*` 子目录中同步更新 `test_*.py`。
4. 运行 `python -m tests.acceptance_matrix.run_acceptance_validation`，查看 Markdown 报告是否能定位失败原因。

## 7. 当前报告

最近一次运行结果：

- Markdown: `reports/acceptance_matrix_report.md`
- JSON: `reports/acceptance_matrix_report.json`

这两个文件是运行产物，可以按需重新生成。
