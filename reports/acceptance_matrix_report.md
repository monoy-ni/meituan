# 8 项业务验收测试报告

- 生成时间: `2026-06-07T21:31:21`
- 测试项总数: `8`
- 通过测试项: `8`
- 失败测试项: `0`
- 测试项通过率: `100.00%`
- 校验项总数: `57`
- 失败校验项: `0`
- 校验项通过率: `100.00%`
- 异常测试项: `0`

## 执行结果总览

| ID | 分类 | 结果 | 失败校验 | 异常 | 主要关联文件 |
| --- | --- | --- | --- | --- | --- |
| AC-01 | 主题确认 | PASS | - | - | activity_agent/modules/dialogue_manager.py<br>activity_agent/agent.py<br>tests/acceptance_matrix/scenario_01_theme_confirmation/test_theme_confirmation_acceptance.py |
| AC-02 | 位置确认 | PASS | - | - | activity_agent/providers/live_sources.py<br>activity_agent/domain/models.py<br>activity_agent/modules/context_collector.py |
| AC-03 | 距离约束 | PASS | - | - | activity_agent/modules/dialogue_manager.py<br>activity_agent/agent.py<br>tests/acceptance_matrix/scenario_03_distance_and_route_requirements/test_distance_route_requirements_acceptance.py |
| AC-04 | POI 搜索 | PASS | - | - | activity_agent/providers/live_sources.py<br>activity_agent/agent.py<br>tests/acceptance_matrix/scenario_04_amap_poi_range_search/test_amap_poi_range_search_acceptance.py |
| AC-05 | 商户组合 | PASS | - | - | activity_agent/tools/mock_meituan.py<br>activity_agent/llm/itinerary_curator.py<br>activity_agent/modules/supply_matcher.py |
| AC-06 | 路径规划 | PASS | - | - | activity_agent/agent.py<br>activity_agent/providers/live_sources.py<br>tests/acceptance_matrix/scenario_06_amap_route_planning/test_amap_route_planning_acceptance.py |
| AC-07 | 体验卡 | PASS | - | - | activity_agent/modules/experience_card_designer.py<br>skill/couple-date-designer/SKILL.md<br>skill/themed-outing-designer/SKILL.md |
| AC-08 | 预约下单 | PASS | - | - | activity_agent/tools/mock_meituan.py<br>activity_agent/modules/booking_orchestrator.py<br>activity_agent/agent.py |

## 问题汇总

- 未发现失败测试项。

## AC-01 AI 多轮交流确认主题

- 分类: `主题确认`
- 结果: `PASS`
- 需求: AI 与用户进行交流确认主题，信息足够后再生成方案。
- 描述: 覆盖模糊开场、场景确认、玩法氛围、预算、时间、默认集合点/距离确认和最终出方案。
- 耗时: `11ms`

### 关联文件

- `activity_agent/modules/dialogue_manager.py`
- `activity_agent/agent.py`
- `tests/acceptance_matrix/scenario_01_theme_confirmation/test_theme_confirmation_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| ambiguous_opening_asks_scene | PASS | choose_scene | choose_scene | 检查 DialogueManager INIT/IDENTIFYING_SCENE 分支。 |
| distance_prompt_before_plan | PASS | 提示默认集合点和距离 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | 检查 DialogueManager._has_location_distance 和默认距离提示。 |
| final_state | PASS | awaiting_selection | awaiting_selection | - |
| options_count | PASS | >=3 | 3 | - |
| budget | PASS | 200 | 200 | - |
| default_origin | PASS | 奥映世纪轩 | 奥映世纪轩 | - |
| default_search_radius | PASS | 5.0 | 5.0 | - |
| route_plan_attached | PASS | 每个方案都有 route_plan | [true, true, true] | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 选项 | 请求快照 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 今晚想出去玩 | 好的！是想和朋友聚聚，还是想安排约会呢？ | identifying_scene | choose_scene | - | {} |
| 2 | 和朋友 | 好的，朋友局！我来帮你安排。帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - | {} |
| 3 | 想放松回血 | 人均预算大概多少呢？100-200、200-300，还是更高一些？ | collecting_friends_context | ask_budget | - | {} |
| 4 | 人均200 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - | {} |
| 5 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - | {} |
| 6 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。<br><br>我给你配了 3 个组局方案：杭州老城烟火半日局 / 运河人文 Citywalk / 西湖轻松打卡局。 | awaiting_selection | select_option | 杭州老城烟火半日局 / 运河人文 Citywalk / 西湖轻松打卡局 | {"scene": "friends", "origin_name": "奥映世纪轩", "origin_address": "民祥路与平澜路交汇处(地铁6号线丰北站C出口)", "origin_amap_url": "https://surl.amap.com/4sRsg3c1oa7b", "origin_longitude": 120.2425, "origin_latitude": 30.2426, "search_radius_km": 5.0, "route_limit_km": 6.0, "route_limit_minutes": 45, "budget_per_person": 200, "time_window": "today 20:00-23:00", "mood_tags": ["回血"], "relationship_stage": null} |

## AC-02 集合位置、高德 IP 定位与默认位置

- 分类: `位置确认`
- 结果: `PASS`
- 需求: 用户信息中需要包括集合位置；支持高德 IP 定位；用户不给位置时默认奥映世纪轩。
- 描述: 覆盖高德 /ip client 参数、默认集合点名称、地址、高德链接和默认坐标。
- 耗时: `5ms`

### 关联文件

- `activity_agent/providers/live_sources.py`
- `activity_agent/domain/models.py`
- `activity_agent/modules/context_collector.py`
- `tests/acceptance_matrix/scenario_02_location_amap_ip_default/test_location_amap_ip_default_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| ip_endpoint | PASS | /ip | https://restapi.amap.com/v3/ip | - |
| ip_param | PASS | 101.68.1.1 | 101.68.1.1 | - |
| ip_key_param | PASS | fake-amap-key | fake-amap-key | - |
| default_origin_name | PASS | 奥映世纪轩 | 奥映世纪轩 | - |
| default_origin_address | PASS | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | - |
| default_amap_url | PASS | https://surl.amap.com/4sRsg3c1oa7b | https://surl.amap.com/4sRsg3c1oa7b | - |
| default_coordinates | PASS | 120.2425,30.2426 | 120.2425,30.2426 | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| amap_ip_payload | {"status": "1", "province": "浙江省", "city": "杭州市", "adcode": "330100"} | - |
| default_request | {"scene": "friends", "origin_name": "奥映世纪轩", "origin_address": "民祥路与平澜路交汇处(地铁6号线丰北站C出口)", "origin_amap_url": "https://surl.amap.com/4sRsg3c1oa7b", "origin_longitude": 120.2425, "origin_latitude": 30.2426, "search_radius_km": 5.0, "route_limit_km": 6.0, "route_limit_minutes": 45, "budget_per_person": 180, "time_window": "today 20:00-23:00", "mood_tags": ["回血"], "relationship_stage": null} | - |

### 工具/外部接口调用记录

| 工具 | 输入摘要 | 输出摘要 |
| --- | --- | --- |
| amap.ip_location | {"ip": "101.68.1.1", "output": "JSON", "key": "fake-amap-key"} | {"status": "1", "province": "浙江省", "city": "杭州市", "adcode": "330100"} |

## AC-03 距离要求与整体路径要求

- 分类: `距离约束`
- 结果: `PASS`
- 需求: 询问用户对距离和整体行程路径长短的要求，并写入最终请求。
- 描述: 覆盖默认距离提示、用户自定义集合点、周边搜索范围、路线公里数和路线分钟数。
- 耗时: `7ms`

### 关联文件

- `activity_agent/modules/dialogue_manager.py`
- `activity_agent/agent.py`
- `tests/acceptance_matrix/scenario_03_distance_and_route_requirements/test_distance_route_requirements_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| distance_prompt | PASS | 提示默认 5km 与 6km/45min | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | - |
| origin_name | PASS | 西湖文化广场 | 西湖文化广场 | - |
| search_radius_km | PASS | 3.0 | 3.0 | - |
| route_limit_km | PASS | 4.0 | 4.0 | - |
| route_limit_minutes | PASS | 40 | 40 | - |
| route_plan_limits | PASS | {"km": 4.0, "minutes": 40} | {"km": 4.0, "minutes": 40} | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| final_request | {"scene": "friends", "origin_name": "西湖文化广场", "origin_address": "西湖文化广场", "origin_amap_url": "", "origin_longitude": null, "origin_latitude": null, "search_radius_km": 3.0, "route_limit_km": 4.0, "route_limit_minutes": 40, "budget_per_person": 180, "time_window": "today 20:00-23:00", "mood_tags": ["回血", "聊天", "低耗社交"], "relationship_stage": null} | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 选项 | 请求快照 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - | {} |
| 2 | 想回血，轻松聊聊天 | 人均预算大概多少呢？100-200、200-300，还是更高一些？ | collecting_friends_context | ask_budget | - | {} |
| 3 | 人均180 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - | {} |
| 4 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - | {} |
| 5 | 从西湖文化广场出发，周边3公里，路线控制在4公里，40分钟内 | 好的！我已经了解得差不多了，这就为你生成几个方案。<br><br>我给你配了 3 个组局方案：西湖轻松打卡局 / 杭州老城烟火半日局 / 运河人文 Citywalk。 | awaiting_selection | select_option | 西湖轻松打卡局 / 杭州老城烟火半日局 / 运河人文 Citywalk | {"scene": "friends", "origin_name": "西湖文化广场", "origin_address": "西湖文化广场", "origin_amap_url": "", "origin_longitude": null, "origin_latitude": null, "search_radius_km": 3.0, "route_limit_km": 4.0, "route_limit_minutes": 40, "budget_per_person": 180, "time_window": "today 20:00-23:00", "mood_tags": ["回血", "聊天", "低耗社交"], "relationship_stage": null} |

## AC-04 高德 POI 范围搜索

- 分类: `POI 搜索`
- 结果: `PASS`
- 需求: 通过高德 POI 在用户给出范围内搜索美食和游乐地点。
- 描述: 覆盖 around location、半径换算、餐饮/游乐关键词、POI 入库和 matched_keywords。
- 耗时: `4ms`

### 关联文件

- `activity_agent/providers/live_sources.py`
- `activity_agent/agent.py`
- `tests/acceptance_matrix/scenario_04_amap_poi_range_search/test_amap_poi_range_search_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| sync_status | PASS | live_synced | live_synced | - |
| around_call_count | PASS | 2 | 2 | - |
| around_location | PASS | 120.2425,30.2426 | ["120.2425,30.2426", "120.2425,30.2426"] | - |
| radius_m | PASS | 3000 | [3000, 3000] | - |
| food_and_fun_keywords | PASS | "{'烧烤', '桌游'}" | "{'烧烤', '桌游'}" | - |
| poi_supplies | PASS | "{'范围测试烧烤店', '范围测试桌游馆'}" | "{'范围测试烧烤店', '范围测试桌游馆'}" | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| sync_result | {"status": "live_synced", "live_places": 2, "sources": {"amap_poi": {"places": 2, "configured": true}, "hangzhou_open_data": {"places": 0, "configured": false}}, "errors": {}, "duration_ms": 0} | - |
| live_supply_names | ["范围测试桌游馆", "范围测试烧烤店"] | - |

### 工具/外部接口调用记录

| 工具 | 输入摘要 | 输出摘要 |
| --- | --- | --- |
| amap.search_pois_around | {"location": "120.2425,30.2426", "radius_m": 3000, "keywords": "烧烤", "city": "330100", "types": "", "offset": 20, "page": 1} | {"status": "1"} |
| amap.search_pois_around | {"location": "120.2425,30.2426", "radius_m": 3000, "keywords": "桌游", "city": "330100", "types": "", "offset": 20, "page": 1} | {"status": "1"} |

## AC-05 mock 美团评价与 LLM 商户组合

- 分类: `商户组合`
- 结果: `PASS`
- 需求: mock 调用美团用户评价和商户介绍，让 LLM 获取适合主题局的商铺、饭店、景点等并组合完整主题局。
- 描述: 覆盖 mock 商户画像、LLM prompt、过滤编造商户 ID、按主题 slots 组合路线。
- 耗时: `0ms`

### 关联文件

- `activity_agent/tools/mock_meituan.py`
- `activity_agent/llm/itinerary_curator.py`
- `activity_agent/modules/supply_matcher.py`
- `activity_agent/modules/itinerary_composer.py`
- `tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection/test_meituan_profiles_llm_selection_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| profile_prompt_contains_reviews | PASS | mock 用户评价摘要 | true | - |
| profile_prompt_contains_intro | PASS | mock 商户介绍 | true | - |
| llm_filters_hallucinated_ids | PASS | made_up_merchant 不进入结果 | ["food_bbq", "activity_ktv", "relax_tea"] | - |
| preferred_ids | PASS | ["food_bbq", "activity_ktv", "relax_tea"] | ["food_bbq", "activity_ktv", "relax_tea"] | - |
| theme_combination_types | PASS | "{'activity', 'dining', 'relax'}" | "{'activity', 'dining', 'relax'}" | - |
| selected_ids_match_llm | PASS | "{'food_bbq', 'activity_ktv', 'relax_tea'}" | "{'food_bbq', 'activity_ktv', 'relax_tea'}" | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| preferred_ids | ["food_bbq", "activity_ktv", "relax_tea"] | - |
| selected_ids | ["activity_ktv", "food_bbq", "relax_tea"] | - |
| llm_prompt_excerpt | {"theme": {"id": "acceptance_recovery", "name": "下班回血主题局", "slots": ["activity", "dining", "relax"]}, "request": {"budget_per_person": 260, "party_size": 4, "mood_tags": ["回血", "解压"], "experience_tags": [], "route_limit_km": 6.0, "route_limit_minutes": 45}, "candidates": [{"id": "food_bbq", "name": "热闹烧烤店", "type": "dining", "price": 98, "distance_km": 1.0, "tags": ["烧烤", "回血"], "matched_keywords": ["烧烤"], "rating": 4.5, "review_summary": "mock 用户评价摘要：氛围 4.5/5，适合聊天/聚会；高峰期建议提前确认座位。", "intro": "热闹烧烤店 mock 商户介绍：适合主题局候选，真实营业、评价和库存需接入授权美团接口后确认。"}, {"id": "activity_ktv", "name": "下班K歌房", "type": ... | - |

### 工具/外部接口调用记录

| 工具 | 输入摘要 | 输出摘要 |
| --- | --- | --- |
| meituan.merchant_profile | {"merchant_id": "food_bbq", "merchant_name": "热闹烧烤店"} | {"merchant_id": "food_bbq", "merchant_name": "热闹烧烤店", "rating": 4.5, "review_count": 908, "intro": "热闹烧烤店 mock 商户介绍：适合主题局候选，真实营业、评价和库存需接入授权美团接口后确认。", "review_summary": "mock 用户评价摘要：氛围 4.5/5，适合聊天/聚会；高峰期建议提前确认座位。", "tags": ["烧烤", "回血"], "data_confidence": "mock"} |
| meituan.merchant_profile | {"merchant_id": "activity_ktv", "merchant_name": "下班K歌房"} | {"merchant_id": "activity_ktv", "merchant_name": "下班K歌房", "rating": 4.2, "review_count": 493, "intro": "下班K歌房 mock 商户介绍：适合主题局候选，真实营业、评价和库存需接入授权美团接口后确认。", "review_summary": "mock 用户评价摘要：氛围 4.2/5，适合聊天/聚会；高峰期建议提前确认座位。", "tags": ["KTV", "解压"], "data_confidence": "mock"} |
| meituan.merchant_profile | {"merchant_id": "relax_tea", "merchant_name": "收尾茶馆"} | {"merchant_id": "relax_tea", "merchant_name": "收尾茶馆", "rating": 4.6, "review_count": 129, "intro": "收尾茶馆 mock 商户介绍：适合主题局候选，真实营业、评价和库存需接入授权美团接口后确认。", "review_summary": "mock 用户评价摘要：氛围 4.6/5，适合聊天/聚会；高峰期建议提前确认座位。", "tags": ["茶馆", "聊天"], "data_confidence": "mock"} |
| llm.preferred_supply_ids | {"candidate_count": 3} | {"merchant_ids": ["food_bbq", "activity_ktv", "relax_tea"]} |

## AC-06 高德路径规划

- 分类: `路径规划`
- 结果: `PASS`
- 需求: 调用高德地图 API 的路径规划工具，给出用户游玩路径。
- 描述: 覆盖每段 walking_route 调用、route_plan legs、总距离、总时长和 within_limits。
- 耗时: `3ms`

### 关联文件

- `activity_agent/agent.py`
- `activity_agent/providers/live_sources.py`
- `tests/acceptance_matrix/scenario_06_amap_route_planning/test_amap_route_planning_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| route_call_count | PASS | 2 | 2 | - |
| route_provider | PASS | amap_route | amap_route | - |
| route_status | PASS | live | live | - |
| legs_count | PASS | 2 | 2 | - |
| total_distance_km | PASS | 2.4 | 2.4 | - |
| total_duration_minutes | PASS | 30 | 30 | - |
| within_limits | PASS | true | true | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| route_plan | {"origin": {"name": "奥映世纪轩", "address": "民祥路与平澜路交汇处(地铁6号线丰北站C出口)", "longitude": 120.2425, "latitude": 30.2426}, "legs": [{"from": "奥映世纪轩", "to": "第一站餐厅", "distance_km": 1.2, "duration_minutes": 15, "mode": "walking", "provider": "amap_route", "message": "AMAP walking leg: 1.2km / 15min."}, {"from": "第一站餐厅", "to": "第二站游乐", "distance_km": 1.2, "duration_minutes": 15, "mode": "walking", "provider": "amap_route", "message": "AMAP walking leg: 1.2km / 15min."}], "total_distance_km": 2.4, "total_duration_minutes": 30, "route_limit_km": 4.0, "route_limit_minutes": 40, "within_limits": true, "provi... | - |

### 工具/外部接口调用记录

| 工具 | 输入摘要 | 输出摘要 |
| --- | --- | --- |
| amap.walking_route | {"origin": "120.2425,30.2426", "destination": "120.25,30.245"} | {"distance": "1200", "duration": "900"} |
| amap.walking_route | {"origin": "120.25,30.245", "destination": "120.26,30.25"} | {"distance": "1200", "duration": "900"} |

## AC-07 情侣/朋友 skill 体验卡

- 分类: `体验卡`
- 结果: `PASS`
- 需求: 情侣使用 couple-date-designer，朋友使用 themed-outing-designer，生成完整的局卡片。
- 描述: 覆盖 designer 字段、卡片必要字段、flow 与 timeline 对齐、预约安全说明。
- 耗时: `12ms`

### 关联文件

- `activity_agent/modules/experience_card_designer.py`
- `skill/couple-date-designer/SKILL.md`
- `skill/themed-outing-designer/SKILL.md`
- `tests/acceptance_matrix/scenario_07_skill_experience_cards/test_skill_experience_cards_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| friend_designer | PASS | themed-outing-designer | themed-outing-designer | - |
| couple_designer | PASS | couple-date-designer | couple-date-designer | - |
| friend_required_keys | PASS | ["booking_note", "designer", "flow", "host_tips", "play_style", "signature_moments", "theme_line", "title", "vibe_tags"] | ["booking_note", "designer", "flow", "host_tips", "play_style", "signature_moments", "theme_line", "title", "vibe_tags"] | - |
| couple_required_keys | PASS | ["booking_note", "designer", "flow", "host_tips", "play_style", "signature_moments", "theme_line", "title", "vibe_tags"] | ["booking_note", "designer", "flow", "host_tips", "play_style", "signature_moments", "theme_line", "title", "vibe_tags"] | - |
| friend_flow_matches_timeline | PASS | 3 | 3 | - |
| couple_flow_matches_timeline | PASS | 3 | 3 | - |
| booking_note_safety | PASS | 确认前不会 | ["玩法卡已生成；下一步只创建预约草稿，用户确认前不会支付或下不可逆订单。", "玩法卡已生成；预约、酒店、礼物和支付都只会进入待确认草稿，确认前不会执行。"] | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| friend_card | {"designer": "themed-outing-designer", "title": "wulin kerry 下班回血局", "theme_line": "把下班后的低电量先接住，再用热闹和夜宵慢慢充回来。", "vibe_tags": ["回血", "夜宵", "低负担"], "play_style": "先卸掉班味，再吃一口热的，最后用一个可进可退的收尾点把聊天留住。", "flow": [{"merchant_id": "act_climbing_001", "merchant_name": "岩点攀岩体验馆", "time": "14:00-15:00", "role": "开局任务", "experience": "开局任务放在「岩点攀岩体验馆」：强互动但不需要尬聊，适合用运动把下班后的疲惫切掉。 这一站负责把回血、夜宵落到真实动作里。"}, {"merchant_id": "dine_bbq_001", "merchant_name": "炭火研究所烤肉", "time": "15:20-16:50", "role": "补给站", "experience": "补给站放在「炭火研究所烤肉」：高满足感、讨论空间足，适合接住活动后的兴奋。 这一站负责把回血、夜宵落到真实动作里。"}, {"merchant_id": "hz_relax_wulin_spa... | - |
| couple_card | {"designer": "couple-date-designer", "title": "初识/暧昧｜轻升温不尴尬约会", "theme_line": "让两个人先舒服地待在同一个节奏里，不急着确认关系。", "vibe_tags": ["低压力", "自然互动", "安全感"], "play_style": "不尴尬破冰，降低压力，增加自然互动", "flow": [{"merchant_id": "act_aroma_001", "merchant_name": "微光香薰 DIY", "time": "10:30-11:45", "role": "安全开场", "experience": "安全开场放在「微光香薰 DIY」：时间不长、表达轻，适合第一次或轻升温约会。 重点是让节奏服务于「不尴尬破冰，降低压力，增加自然互动」。"}, {"merchant_id": "dine_safe_cafe_001", "merchant_name": "橙花咖啡甜品", "time": "12:05-13:15", "role": "自然升温", "experience": "自然升温放在「橙花咖啡甜品」：轻、短、好退出，适合低压力邀约。 重点是让节奏服务于「不尴尬破冰，降低压力，增加自然互动」。"}, {"merchant_id": "night_riverside_001"... | - |

## AC-08 mock 美团预约与下单

- 分类: `预约下单`
- 结果: `PASS`
- 需求: mock 调用美团 API 完成预约和下单验证，同时保持确认前安全边界。
- 描述: 覆盖可用性检查、booking hold、AA 草稿、取消不下单、确认后生成 mock 订单。
- 耗时: `8ms`

### 关联文件

- `activity_agent/tools/mock_meituan.py`
- `activity_agent/modules/booking_orchestrator.py`
- `activity_agent/agent.py`
- `tests/acceptance_matrix/scenario_08_mock_booking_order/test_mock_booking_order_acceptance.py`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 定位提示 |
| --- | --- | --- | --- | --- |
| draft_status | PASS | pending_user_confirmation | pending_user_confirmation | - |
| confirmation_required | PASS | true | true | - |
| safety_notice | PASS | 不会未经授权支付 | 半自动确认模式：Agent 可以生成待确认订单和 AA 方案，但不会未经授权支付或下不可逆订单。 | - |
| aa_draft_created | PASS | true | true | - |
| cancel_no_order | PASS | cancelled | cancelled | - |
| confirm_creates_orders | PASS | mock order ids | ["order_d2393610", "order_8ddb25e6", "order_314e659f"] | - |
| availability_called_per_item | PASS | >=3 | 3 | - |
| hold_called | PASS | create_booking_hold | ["check_availability", "check_availability", "check_availability", "create_booking_hold", "create_aa_draft", "confirm_booking"] | - |
| aa_called | PASS | create_aa_draft | ["check_availability", "check_availability", "check_availability", "create_booking_hold", "create_aa_draft", "confirm_booking"] | - |
| confirm_called | PASS | confirm_booking | ["check_availability", "check_availability", "check_availability", "create_booking_hold", "create_aa_draft", "confirm_booking"] | - |

### 证据

| 名称 | 值 | 说明 |
| --- | --- | --- |
| draft | {"id": "draft_1fdc3d3792da", "status": "pending_user_confirmation", "items": 3, "aa_draft": {"aa_id": "aa_1c62644dcc", "total": 1128, "party_size": 4, "per_person": 282, "mode": "aa_prepay", "status": "draft"}} | - |
| cancelled | {"status": "cancelled", "order_ids": []} | - |
| confirmed | {"status": "confirmed", "order_ids": ["order_d2393610", "order_8ddb25e6", "order_314e659f"]} | - |

### 工具/外部接口调用记录

| 工具 | 输入摘要 | 输出摘要 |
| --- | --- | --- |
| check_availability | {} | {} |
| check_availability | {} | {} |
| check_availability | {} | {} |
| create_booking_hold | {} | {} |
| create_aa_draft | {} | {} |
| confirm_booking | {} | {} |
