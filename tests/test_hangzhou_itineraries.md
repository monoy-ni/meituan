# test_hangzhou_itineraries.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_hangzhou_itineraries.py](file:///d:/meituan%20agent/tests/test_hangzhou_itineraries.py)

这个文件是杭州本地路线和高德能力相关测试的主文件，覆盖杭州主题规划、关键词扩展、高德地图/天气 provider、主题 POI 同步和 booking 安全边界等内容。

## 2. 主要覆盖内容

本文件重点验证：

1. 杭州老城、运河、近郊、雨天室内等主题是否能正确命中
2. 低预算下是否还能维持完整闭环路线
3. 关键词种子表是否按朋友局/情侣局场景正确工作
4. LLM 关键词扩展是否接受相关词、拒绝无关词
5. 高德路线与天气 provider 是否能返回 live 数据
6. Hybrid provider 是否能把高德 POI 同步进 catalog
7. 周边 5 公里 around 搜索是否生效
8. booking draft 是否在确认前保持安全

## 3. 关键测试分组

### 杭州主题规划

包括：

- 老城烟火半日局
- 龙坞茶山近郊局
- 雨天室内低耗局
- 运河人文 Citywalk
- 低预算杭州特色美食局

这组测试主要验证杭州主题是否被正确规划。

### 关键词种子与扩展

包括：

- 朋友局关键词种子
- 情侣局关键词种子
- 纪念日/关系阶段关键词映射
- LLM 关键词扩展合法性校验

这组测试主要验证主题规划前的关键词构造是否可靠。

### 高德 Provider 与 Hybrid 数据

包括：

- `AmapMapDataProvider`
- `AmapWeatherProvider`
- `HybridLiveDataProvider.sync_live_sources()`
- `HybridLiveDataProvider.sync_theme_pois()`

这组测试主要验证 live provider 接入点和 seed/hybrid 模式的行为。

### 路线与预约安全

包括：

- `route_plan` 是否附着到方案
- booking draft 是否保持待确认状态

## 4. 测试价值

这个文件相当于“杭州本地玩法能力”的综合回归测试。

如果它失败，可能说明以下方向发生了问题：

- 杭州主题命中逻辑回归
- 关键词扩展失效
- 高德 provider 集成有问题
- POI 同步能力失效
- 路线规划或预约安全边界异常

## 5. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_hangzhou_itineraries
```

## 6. 建议重点关注的用例

建议重点关注以下几类：

1. 杭州主题是否命中正确
2. `test_no_map_api_key_degrades_to_seed_refresh`
3. `test_amap_route_and_weather_providers_use_live_payloads`
4. `test_hybrid_provider_syncs_amap_pois_into_catalog`
5. `test_theme_poi_sync_uses_amap_around_and_merges_matched_keywords`
6. `test_couple_flow_uses_same_keyword_expansion_and_amap_around_search`

## 7. 通过标准

通过标准包括：

1. 杭州主题路线生成正确
2. 高德 provider 和 hybrid provider 行为正确
3. 关键词扩展逻辑稳定
4. booking draft 仍保持确认前安全边界
