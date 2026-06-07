# 06 高德路径规划验收

## 目标

验证系统会调用高德路径规划工具，为集合点到各游玩节点生成路径、距离、时长和是否满足路线限制。

## 覆盖点

- 每一段路径都调用 `walking_route(origin, destination)`
- 路径结果写入 `route_plan.legs`
- 总距离、总时长、provider/status 正确
- 结果保留用户的路线公里数与分钟数限制

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_06_amap_route_planning
```
