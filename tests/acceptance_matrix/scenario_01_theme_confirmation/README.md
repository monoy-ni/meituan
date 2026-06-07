# 01 主题确认对话验收

## 目标

验证 AI 会先通过多轮交流确认用户的场景和主题方向，收集预算、时间、集合点/距离等关键信息后，再生成完整方案，而不是一开始就直接出卡片。

## 覆盖点

- 模糊首轮输入先进入场景确认
- 朋友局确认后继续收集玩法氛围、预算、时间
- 缺少集合点和距离要求时先提示默认值
- 用户接受默认值后生成 3 个方案
- 最终进入 `awaiting_selection`

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_01_theme_confirmation
```
