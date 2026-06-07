# 04 高德 POI 范围搜索验收

## 目标

验证系统会根据用户给出的集合点坐标和搜索范围，调用高德 `place/around` 搜索美食和游乐地点，并把结果同步到本地供给目录。

## 覆盖点

- 经纬度被转换成高德 around 的 `location`
- 公里半径被转换成米
- 美食和游乐关键词都会触发 around 搜索
- 返回 POI 被写入 `amap_poi` 供给，并保留 matched keywords

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_04_amap_poi_range_search
```
