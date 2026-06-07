# tests 目录说明

`tests/` 目录同时包含普通 unittest、专项验证 harness、默认用例集，以及部分测试文件的配套 Markdown 说明。

更完整的全局测试入口见 [`../docs/testing.md`](../docs/testing.md)。

## 快速命令

```powershell
# 全量测试
python -m unittest discover tests

# 主业务链路
python -m unittest tests.test_activity_agent tests.test_guided_conversation tests.test_experience_cards

# 杭州/高德相关
python -m unittest tests.test_hangzhou_itineraries tests.test_amap_poi_range

# SDK 与基础设施
python -m unittest tests.test_mvp_sdk

# 主题确认专项验证
python -m tests.run_theme_confirmation_validation

# 位置确认专项验证
python -m tests.run_location_confirmation_test

# 8 项业务验收测试矩阵
python -m unittest discover tests/acceptance_matrix
```

## 文件地图

| 文件 | 类型 | 说明 |
| --- | --- | --- |
| [`acceptance_matrix/`](acceptance_matrix/) | 验收矩阵 | 8 项业务验收测试集中目录，每项一个子目录，包含 README 和 test 文件 |
| [`test_activity_agent.py`](test_activity_agent.py) | unittest | Agent 主链路：方案、反馈、调整、预约草稿、复盘 |
| [`test_activity_agent.md`](test_activity_agent.md) | 说明 | `test_activity_agent.py` 的覆盖范围、关键用例和通过标准 |
| [`test_guided_conversation.py`](test_guided_conversation.py) | unittest | 多轮引导式对话、对话状态、上下文追加、再规划 |
| [`test_guided_conversation.md`](test_guided_conversation.md) | 说明 | `test_guided_conversation.py` 的覆盖范围、关键用例和通过标准 |
| [`test_experience_cards.py`](test_experience_cards.py) | unittest | 体验卡/玩法卡、安全兜底、接口 payload |
| [`test_experience_cards.md`](test_experience_cards.md) | 说明 | `test_experience_cards.py` 的覆盖范围、关键用例和通过标准 |
| [`test_hangzhou_itineraries.py`](test_hangzhou_itineraries.py) | unittest | 杭州主题路线、关键词扩展、高德 provider、Hybrid POI |
| [`test_hangzhou_itineraries.md`](test_hangzhou_itineraries.md) | 说明 | `test_hangzhou_itineraries.py` 的覆盖范围、关键分组和通过标准 |
| [`test_amap_poi_range.py`](test_amap_poi_range.py) | unittest | 高德 around 搜索、用户半径传递、餐饮/游乐 POI 同步 |
| [`test_amap_poi_range.md`](test_amap_poi_range.md) | 说明 | `test_amap_poi_range.py` 的覆盖范围、关键用例和通过标准 |
| [`test_mvp_sdk.py`](test_mvp_sdk.py) | unittest | 环境变量、LLM client、SQLite 持久化、跨实例恢复 |
| [`test_mvp_sdk.md`](test_mvp_sdk.md) | 说明 | `test_mvp_sdk.py` 的覆盖范围、关键用例和通过标准 |
| [`test_theme_confirmation_validation.py`](test_theme_confirmation_validation.py) | unittest | 主题确认验证 harness 的集成入口和异常捕获测试 |
| [`theme_confirmation_harness.py`](theme_confirmation_harness.py) | harness | 主题确认多轮对话执行器、校验器、报告生成器 |
| [`theme_confirmation_cases.py`](theme_confirmation_cases.py) | cases | 主题确认默认用例集 |
| [`run_theme_confirmation_validation.py`](run_theme_confirmation_validation.py) | runner | 主题确认专项验证快速入口 |
| [`test_location_confirmation.py`](test_location_confirmation.py) | unittest | 位置确认验证 harness 的集成入口和基础容错测试 |
| [`location_confirmation_harness.py`](location_confirmation_harness.py) | harness | 位置确认多轮对话执行器、指标统计、报告生成器 |
| [`location_confirmation_cases.py`](location_confirmation_cases.py) | cases | 位置确认默认用例集 |
| [`run_location_confirmation_test.py`](run_location_confirmation_test.py) | runner | 位置确认专项验证快速入口 |

## 配套文档

| 文档 | 说明 |
| --- | --- |
| [`../docs/testing.md`](../docs/testing.md) | 测试说明总览和运行策略 |
| [`../docs/theme_confirmation_validation_guide.md`](../docs/theme_confirmation_validation_guide.md) | 主题确认专项验证完整使用说明 |
| [`../docs/location_confirmation_validation_guide.md`](../docs/location_confirmation_validation_guide.md) | 位置确认与高德集成专项验证完整使用说明 |
| [`../theme-confirmation-test.md`](../theme-confirmation-test.md) | 主题确认节点手工验收、接口级测试和前端联调检查 |

## 维护规则

1. 新增独立测试文件时，优先补充同名 `test_xxx.md`。
2. 新增专项 harness 或 runner 时，同步更新本 README 和 [`../docs/testing.md`](../docs/testing.md)。
3. 修改报告输出路径、运行命令或环境依赖时，同步更新对应说明文档。
4. `reports/` 是运行产物目录，不放在 `tests/` 下维护。
