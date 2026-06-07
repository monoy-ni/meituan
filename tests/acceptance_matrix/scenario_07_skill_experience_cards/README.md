# 07 情侣/朋友 skill 体验卡验收

## 目标

验证朋友局使用 `themed-outing-designer`，情侣约会使用 `couple-date-designer`，并生成完整的主题局/约会体验卡。

## 覆盖点

- 朋友局卡片 designer 为 `themed-outing-designer`
- 情侣局卡片 designer 为 `couple-date-designer`
- 卡片包含标题、主题线、玩法、流程、记忆点、host tips、预约说明
- 卡片 flow 引用真实 timeline item，不编造空流程

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_07_skill_experience_cards
```
