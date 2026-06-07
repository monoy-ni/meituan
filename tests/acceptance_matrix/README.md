# 8 项验收测试矩阵

这个目录把当前产品要求拆成 8 个可独立运行的验收测试。每个子目录对应一个验收点，包含：

- `README.md`：说明测试目标、覆盖点和运行命令
- `test_*.py`：对应的可执行 unittest

旧的 `tests/test_*.py` 仍保留作为单元/回归测试；这里是更面向业务验收的集中入口。

## 运行方式

推荐先运行诊断报告入口：

```powershell
python -m tests.acceptance_matrix.run_acceptance_validation
```

运行后会生成：

- `reports/acceptance_matrix_report.md`
- `reports/acceptance_matrix_report.json`

如果只需要跑 unittest，从项目根目录执行：

```powershell
python -m unittest discover tests/acceptance_matrix
```

也可以单独运行某一项：

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_01_theme_confirmation
python -m unittest discover tests/acceptance_matrix/scenario_02_location_amap_ip_default
python -m unittest discover tests/acceptance_matrix/scenario_03_distance_and_route_requirements
python -m unittest discover tests/acceptance_matrix/scenario_04_amap_poi_range_search
python -m unittest discover tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection
python -m unittest discover tests/acceptance_matrix/scenario_06_amap_route_planning
python -m unittest discover tests/acceptance_matrix/scenario_07_skill_experience_cards
python -m unittest discover tests/acceptance_matrix/scenario_08_mock_booking_order
```

## 目录映射

| 序号 | 子目录 | 验收点 |
| --- | --- | --- |
| 1 | [`scenario_01_theme_confirmation`](scenario_01_theme_confirmation/) | AI 与用户多轮交流，确认朋友/情侣场景、主题方向和关键信息后再出方案 |
| 2 | [`scenario_02_location_amap_ip_default`](scenario_02_location_amap_ip_default/) | 用户信息包含集合位置；高德 IP 定位接口可 mock；用户不给位置时默认奥映世纪轩 |
| 3 | [`scenario_03_distance_and_route_requirements`](scenario_03_distance_and_route_requirements/) | 询问集合点、搜索范围、整体路径长度/时间，并写入请求 |
| 4 | [`scenario_04_amap_poi_range_search`](scenario_04_amap_poi_range_search/) | 按用户范围调用高德 POI around 搜索美食和游乐地点 |
| 5 | [`scenario_05_meituan_profiles_llm_selection`](scenario_05_meituan_profiles_llm_selection/) | mock 美团用户评价和商户介绍进入 LLM 商户组合器，并产出主题局组合 |
| 6 | [`scenario_06_amap_route_planning`](scenario_06_amap_route_planning/) | 调用高德路径规划生成游玩路径、距离和时长 |
| 7 | [`scenario_07_skill_experience_cards`](scenario_07_skill_experience_cards/) | 情侣走 `couple-date-designer`，朋友走 `themed-outing-designer`，生成完整局卡片 |
| 8 | [`scenario_08_mock_booking_order`](scenario_08_mock_booking_order/) | mock 调用美团预约、hold、AA 草稿、确认下单；确认前保持安全边界 |

## 当前补齐情况

已有回归测试覆盖了大部分能力。本次新增的明确缺口是高德 `ip_location()` client 封装及其 mock 测试，避免“IP 定位”只停留在文档要求里。

完整使用说明见 [`../../docs/acceptance_matrix_validation_guide.md`](../../docs/acceptance_matrix_validation_guide.md)。
