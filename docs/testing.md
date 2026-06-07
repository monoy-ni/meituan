# 测试说明总览

本文档是测试相关 Markdown 的统一入口，用来说明每类测试覆盖什么、应该跑哪条命令、以及详细说明分散在哪些文件中。

## 文档分层

| 层级 | 位置 | 作用 |
| --- | --- | --- |
| 测试总览 | `docs/testing.md` | 当前入口页，给出测试分类、运行命令和文档索引 |
| 测试目录索引 | [`../tests/README.md`](../tests/README.md) | 面向 `tests/` 目录的文件地图 |
| 单文件测试说明 | [`../tests/test_*.md`](../tests/) | 解释对应 `test_*.py` 的覆盖范围、关键用例和通过标准 |
| 专项验证指南 | [`theme_confirmation_validation_guide.md`](theme_confirmation_validation_guide.md)、[`location_confirmation_validation_guide.md`](location_confirmation_validation_guide.md) | 解释带 harness、cases、报告产物的专项验证套件 |
| 手工/接口验收清单 | [`../theme-confirmation-test.md`](../theme-confirmation-test.md) | 主题确认节点的接口级与前端联调验收说明 |
| 运行产物 | [`../reports/`](../reports/) | 专项验证生成的 Markdown / JSON 报告，不作为源说明维护 |

## 快速运行

从项目根目录执行。

```powershell
# 全量 unittest
python -m unittest discover tests

# 主业务链路回归
python -m unittest tests.test_activity_agent tests.test_guided_conversation tests.test_experience_cards

# 杭州本地化、高德地图和 POI 链路
python -m unittest tests.test_hangzhou_itineraries tests.test_amap_poi_range

# SDK、配置、持久化与基础设施
python -m unittest tests.test_mvp_sdk

# 主题确认专项验证，生成 reports/theme_confirmation_report.*
python -m tests.run_theme_confirmation_validation

# 位置确认专项验证，生成 reports/location_confirmation_report.*
python -m tests.run_location_confirmation_test

# 8 项业务验收测试矩阵，生成 reports/acceptance_matrix_report.*
python -m tests.acceptance_matrix.run_acceptance_validation

# 8 项验收矩阵的 unittest 入口
python -m unittest discover tests/acceptance_matrix
```

## 8 项业务验收测试矩阵

集中目录：[`../tests/acceptance_matrix/`](../tests/acceptance_matrix/)
完整指南：[`acceptance_matrix_validation_guide.md`](acceptance_matrix_validation_guide.md)

这组测试按当前产品验收点拆成 8 个子目录，每个子目录都有 `README.md` 和 `test_*.py`。同时提供 `acceptance_validation_harness.py`、`acceptance_validation_cases.py` 和 `run_acceptance_validation.py`，运行后会生成可定位问题的 Markdown / JSON 报告。

| 序号 | 子目录 | 验收点 | 单独运行 |
| --- | --- | --- | --- |
| 1 | [`scenario_01_theme_confirmation`](../tests/acceptance_matrix/scenario_01_theme_confirmation/) | AI 与用户多轮交流确认主题后再出方案 | `python -m unittest discover tests/acceptance_matrix/scenario_01_theme_confirmation` |
| 2 | [`scenario_02_location_amap_ip_default`](../tests/acceptance_matrix/scenario_02_location_amap_ip_default/) | 集合位置、高德 IP 定位 client、默认奥映世纪轩 | `python -m unittest discover tests/acceptance_matrix/scenario_02_location_amap_ip_default` |
| 3 | [`scenario_03_distance_and_route_requirements`](../tests/acceptance_matrix/scenario_03_distance_and_route_requirements/) | 询问周边搜索范围和整体路径长短/耗时 | `python -m unittest discover tests/acceptance_matrix/scenario_03_distance_and_route_requirements` |
| 4 | [`scenario_04_amap_poi_range_search`](../tests/acceptance_matrix/scenario_04_amap_poi_range_search/) | 在用户给出范围内调用高德 POI around 搜索美食和游乐 | `python -m unittest discover tests/acceptance_matrix/scenario_04_amap_poi_range_search` |
| 5 | [`scenario_05_meituan_profiles_llm_selection`](../tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection/) | mock 美团评价/商户介绍进入 LLM 商户组合器 | `python -m unittest discover tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection` |
| 6 | [`scenario_06_amap_route_planning`](../tests/acceptance_matrix/scenario_06_amap_route_planning/) | 调用高德路径规划生成游玩路径 | `python -m unittest discover tests/acceptance_matrix/scenario_06_amap_route_planning` |
| 7 | [`scenario_07_skill_experience_cards`](../tests/acceptance_matrix/scenario_07_skill_experience_cards/) | 情侣/朋友分别使用对应 skill 生成完整局卡片 | `python -m unittest discover tests/acceptance_matrix/scenario_07_skill_experience_cards` |
| 8 | [`scenario_08_mock_booking_order`](../tests/acceptance_matrix/scenario_08_mock_booking_order/) | mock 美团预约、hold、AA 草稿、确认下单与安全边界 | `python -m unittest discover tests/acceptance_matrix/scenario_08_mock_booking_order` |

## 自动化测试索引

| 测试文件 | 详细说明 | 主要覆盖 | 推荐命令 |
| --- | --- | --- | --- |
| [`../tests/test_activity_agent.py`](../tests/test_activity_agent.py) | [`../tests/test_activity_agent.md`](../tests/test_activity_agent.md) | Agent 主业务流：生成方案、反馈收敛、改方案、预约草稿、复盘 | `python -m unittest tests.test_activity_agent` |
| [`../tests/test_guided_conversation.py`](../tests/test_guided_conversation.py) | [`../tests/test_guided_conversation.md`](../tests/test_guided_conversation.md) | 多轮引导式对话、状态元数据、上下文追加与再规划 | `python -m unittest tests.test_guided_conversation` |
| [`../tests/test_experience_cards.py`](../tests/test_experience_cards.py) | [`../tests/test_experience_cards.md`](../tests/test_experience_cards.md) | 体验卡/玩法卡生成、商户 ID 兜底、预约前置保护、接口暴露 | `python -m unittest tests.test_experience_cards` |
| [`../tests/test_hangzhou_itineraries.py`](../tests/test_hangzhou_itineraries.py) | [`../tests/test_hangzhou_itineraries.md`](../tests/test_hangzhou_itineraries.md) | 杭州主题路线、关键词扩展、高德 provider、Hybrid POI、预约安全 | `python -m unittest tests.test_hangzhou_itineraries` |
| [`../tests/test_amap_poi_range.py`](../tests/test_amap_poi_range.py) | [`../tests/test_amap_poi_range.md`](../tests/test_amap_poi_range.md) | 高德 around 搜索、用户半径传递、餐饮/游乐 POI 合并 | `python -m unittest tests.test_amap_poi_range` |
| [`../tests/test_mvp_sdk.py`](../tests/test_mvp_sdk.py) | [`../tests/test_mvp_sdk.md`](../tests/test_mvp_sdk.md) | 环境变量、LLM client、SQLite 持久化、跨实例恢复、酒店/礼物草稿 | `python -m unittest tests.test_mvp_sdk` |
| [`../tests/test_theme_confirmation_validation.py`](../tests/test_theme_confirmation_validation.py) | [`theme_confirmation_validation_guide.md`](theme_confirmation_validation_guide.md) | 主题确认 harness 可执行、报告生成、超时/异常/格式错误捕获 | `python -m unittest tests.test_theme_confirmation_validation` |
| [`../tests/test_location_confirmation.py`](../tests/test_location_confirmation.py) | [`location_confirmation_validation_guide.md`](location_confirmation_validation_guide.md) | 位置确认默认值、显式位置、高德 URL、坐标字段、无效位置容错 | `python -m unittest tests.test_location_confirmation` |

## 专项验证套件

### 主题确认验证

相关文件：

| 文件 | 作用 |
| --- | --- |
| [`../tests/theme_confirmation_harness.py`](../tests/theme_confirmation_harness.py) | 执行多轮对话用例、校验结果、生成 Markdown / JSON 报告 |
| [`../tests/theme_confirmation_cases.py`](../tests/theme_confirmation_cases.py) | 默认主题确认用例集，共 10 条 |
| [`../tests/run_theme_confirmation_validation.py`](../tests/run_theme_confirmation_validation.py) | 快速运行入口 |
| [`../tests/test_theme_confirmation_validation.py`](../tests/test_theme_confirmation_validation.py) | unittest 集成入口，重点覆盖 harness 可执行性和异常捕获 |
| [`theme_confirmation_validation_guide.md`](theme_confirmation_validation_guide.md) | 完整使用说明、报告解读、自定义用例方式 |
| [`../theme-confirmation-test.md`](../theme-confirmation-test.md) | 主题确认节点的手工验收与接口联调清单 |

运行后会生成：

- `reports/theme_confirmation_report.md`
- `reports/theme_confirmation_report.json`

### 位置确认与高德集成验证

相关文件：

| 文件 | 作用 |
| --- | --- |
| [`../tests/location_confirmation_harness.py`](../tests/location_confirmation_harness.py) | 执行位置确认对话用例、汇总位置/坐标/API 指标、生成报告 |
| [`../tests/location_confirmation_cases.py`](../tests/location_confirmation_cases.py) | 默认位置确认用例集，共 13 条 |
| [`../tests/run_location_confirmation_test.py`](../tests/run_location_confirmation_test.py) | 快速运行入口 |
| [`../tests/test_location_confirmation.py`](../tests/test_location_confirmation.py) | unittest 集成入口，覆盖默认位置、显式位置、异常容错 |
| [`location_confirmation_validation_guide.md`](location_confirmation_validation_guide.md) | 完整使用说明、环境配置、报告解读、自定义用例方式 |

运行后会生成：

- `reports/location_confirmation_report.md`
- `reports/location_confirmation_report.json`

## 什么时候跑哪一组

| 改动类型 | 建议测试 |
| --- | --- |
| 改 `activity_agent/agent.py`、规划主流程、反馈、预约、复盘 | `tests.test_activity_agent`、`tests.test_guided_conversation`、`tests.test_experience_cards` |
| 改对话状态机、`DialogueManager`、`ContextCollector` | `tests.test_guided_conversation`、`tests.test_theme_confirmation_validation`、必要时跑主题确认专项验证 |
| 改体验卡、设计器、前端 option payload | `tests.test_experience_cards` |
| 改杭州主题、关键词种子、高德 provider、路线/天气/POI | `tests.test_hangzhou_itineraries`、`tests.test_amap_poi_range` |
| 改位置解析、默认集合点、高德 URL/坐标 | `tests.test_location_confirmation`、必要时跑位置确认专项验证 |
| 改 8 个业务验收点任一链路 | `python -m tests.acceptance_matrix.run_acceptance_validation` |
| 改配置、LLM 客户端、SQLite 存储、session 恢复 | `tests.test_mvp_sdk` |
| 发布或合并前做回归 | `python -m unittest discover tests`，再按风险追加两个专项验证入口 |

## 维护规则

新增或调整测试时，按下面规则同步文档：

1. 新增 `tests/test_xxx.py` 后，如果它是独立测试主题，补充 `tests/test_xxx.md`。
2. 新增 harness / cases / run 脚本后，把它登记到本文档的“专项验证套件”。
3. 调整测试命令、报告路径或环境变量后，同步更新本文档和对应专项指南。
4. `reports/` 下是运行产物，可以被重新生成；不要把报告内容当作长期源说明维护。
