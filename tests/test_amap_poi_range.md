# test_amap_poi_range.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_amap_poi_range.py](file:///d:/meituan%20agent/tests/test_amap_poi_range.py)

这个文件是针对“高德地图 POI 在用户给定范围内搜索美食和游乐地点”的独立测试文件。

它比 `test_hangzhou_itineraries.py` 更聚焦，只验证“范围搜索”这一条链路。

## 2. 主要覆盖内容

本文件重点验证：

1. Provider 层是否会使用高德 `search_pois_around()`
2. 用户给出的 `search_radius_km` 是否会正确换算成米
3. 起点经纬度是否会正确传给高德 around 搜索
4. 美食类和游乐类关键词是否都会触发 around 搜索
5. 高德返回的 POI 是否会写回为 `amap_poi`
6. Agent 层是否能把“周边 5 公里”传入整条规划链路

## 3. 关键测试点

### `test_provider_searches_food_and_fun_within_user_radius`

- 直接测试 `HybridLiveDataProvider.sync_theme_pois()`
- 验证 `烧烤` 和 `桌游` 两类关键词都会触发 around 搜索
- 验证 `5 km -> 5000 m`
- 验证返回的餐饮和游乐 POI 会进入 live supplies

### `test_agent_passes_search_radius_into_amap_around_chain`

- 直接测试 `ActivityPlanningAgent.generate_itineraries()`
- 验证用户输入“周边5公里，想和朋友找烧烤和能玩的地方”后
- Agent 会把半径和关键词一路传到高德 around 搜索
- 验证结果仍能生成 `search_keywords` 和 `route_plan`

## 4. 测试设计说明

这个文件使用了 `FakeAmapRangeClient`，因此：

- 不依赖真实高德 Key
- 不依赖真实网络
- 可以稳定验证参数传递和调用路径

这种设计适合本地自动化测试和 CI。

## 5. 测试价值

这个文件主要防止以下问题回归：

1. 用户输入了范围，但系统没有走 around 搜索
2. 半径单位传错，公里没有转换成米
3. 只搜到了美食，没搜到游乐
4. POI 返回了，但没有进入供给 catalog
5. Agent 层没有把搜索半径传到底层 provider

## 6. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_amap_poi_range
```

如果只跑单条用例，可执行：

```powershell
python -m unittest tests.test_amap_poi_range.AmapPoiRangeTest.test_provider_searches_food_and_fun_within_user_radius
python -m unittest tests.test_amap_poi_range.AmapPoiRangeTest.test_agent_passes_search_radius_into_amap_around_chain
```

## 7. 通过标准

通过标准包括：

1. around 搜索被真实触发
2. 搜索半径换算正确
3. 美食和游乐关键词都被覆盖
4. Provider 和 Agent 两层链路都通过
