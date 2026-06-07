# 03 距离与整体路径要求验收

## 目标

验证对话会询问用户对集合点、周边搜索范围和整体行程路径长短/耗时的要求，并把用户给出的限制写入最终请求。

## 覆盖点

- 信息齐全但未给位置/距离时，系统提示默认集合点和默认范围
- 用户可覆盖集合点、周边搜索半径、路线公里数、路线分钟数
- 最终方案带有 `route_plan`

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_03_distance_and_route_requirements
```
