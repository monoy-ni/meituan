# 杭州活动规划 Agent 工具调用链路

## 1. 文档目的

本文档说明整个 `activity_agent` 项目中的工具调用链路，重点回答以下问题：

1. 用户请求是如何从前端进入后端的。
2. `ActivityPlanningAgent` 在规划、刷新、预约时分别会调用哪些模块。
3. Provider 层和 Tool 层分别承担什么职责。
4. 当前 mock 工具是如何被包装和调用的。
5. 工具调用结果如何回传给上层接口和前端。

这份文档写的是整个 Agent 的调用链路，而不是某个单独 skill 的逻辑。

## 2. 工具调用的总体分层

项目里的“工具调用”不是直接从接口跳到第三方服务，而是经过多层封装。

总体分层如下：

```text
前端 / Demo / SDK 调用
→ FastAPI 接口层
→ ActivityPlanningAgent
→ 业务模块层
→ Provider 层
→ Tool Client / Mock Tool
→ 返回 ToolResult / ProviderSnapshot
→ 组装成 AgentResponse 或业务结果
→ 后端接口序列化后返回前端
```

更具体一点：

```text
React 前端 / demo.py
→ backend/main.py
→ activity_agent/agent.py
→ modules/*
→ providers/*
→ tools/mock_meituan.py
```

## 3. 核心参与方说明

### 3.1 接口层

文件：

- [main.py](file:///d:/meituan%20agent/backend/main.py)

职责：

- 提供 REST API
- 接收前端请求
- 调用 `ActivityPlanningAgent`
- 将内部对象转换成 JSON 响应
- 处理 `ValueError -> HTTPException`

### 3.2 Agent 门面层

文件：

- [agent.py](file:///d:/meituan%20agent/activity_agent/agent.py)

职责：

- 作为整个系统的统一入口
- 编排规划、反馈、预约、刷新、复盘等流程
- 连接业务模块、provider、repository
- 决定什么时候调用哪个工具

### 3.3 业务模块层

目录：

- `activity_agent/modules/`

职责：

- 做规划逻辑，不直接访问外部接口
- 例如：
  - `IntentRouter`：识别意图
  - `ContextCollector`：抽取请求
  - `ThemePlanner`：选主题
  - `SupplyMatcher`：匹配供给
  - `ItineraryComposer`：组装路线
  - `FeedbackResolver`：根据反馈收敛方案
  - `BookingOrchestrator`：生成预约草稿与确认

### 3.4 Provider 层

文件：

- [local_data.py](file:///d:/meituan%20agent/activity_agent/providers/local_data.py)

职责：

- 把“数据源能力”包装成统一接口
- 对上层隐藏底层数据是否来自 seed、本地缓存还是外部 provider

主要 provider：

- `SeedLocalDataProvider`
- `MockMapDataProvider`
- `MockWeatherProvider`
- `MockCommerceProvider`

### 3.5 Tool 层

文件：

- [mock_meituan.py](file:///d:/meituan%20agent/activity_agent/tools/mock_meituan.py)

职责：

- 模拟外部美团能力
- 输出统一的 `ToolResult`
- 每次工具调用都生成 `ToolEvent`

当前 mock 工具支持：

- `search_merchants`
- `merchant_profile`
- `check_availability`
- `create_booking_hold`
- `create_aa_draft`
- `confirm_booking`

## 4. 规划主链路

这是最核心的一条调用路径，发生在用户首次生成方案时。

### 4.1 入口

常见入口有三种：

- `POST /api/chat`
- `POST /api/chat/guided`
- `POST /api/itineraries/generate`

对应文件：

- [main.py](file:///d:/meituan%20agent/backend/main.py)

### 4.2 标准规划链路

标准的 `chat()` 链路如下：

```text
前端/客户端
→ POST /api/chat
→ backend.main.chat()
→ ActivityPlanningAgent.chat()
→ repository.add_message()
→ ActivityPlanningAgent.plan()
→ IntentRouter.route()
→ ContextCollector.collect()
→ _merge_llm_data()（可选）
→ _apply_adjustments()
→ ThemePlanner.plan()
→ ItineraryComposer.compose()
→ SupplyMatcher.match_slot() × N
→ ShareCardGenerator.render() × N
→ repository.save_planning_result()
→ 返回 AgentResponse
→ backend.main._response_payload()
→ JSON 返回前端
```

### 4.3 这条链路里“工具”在哪

在纯 seed 规划模式下，严格意义上的外部工具调用很少，主要依赖本地供给和规则模块。

但当进入带候选 enrich 的链路时，会额外调用 commerce provider 获取商户画像：

```text
ActivityPlanningAgent._enrich_theme_candidates_with_mock_profiles()
→ commerce_provider.merchant_profile()
→ MockCommerceProvider.merchant_profile()
→ MockMeituanToolClient.merchant_profile()
→ 返回 ToolResult + ToolEvent
```

这说明：

- 规划主链路本身更多依赖本地 catalog
- 工具层更多在“补充上下文”和“预约阶段”中发挥作用

## 5. 主题 POI 补充链路

在更完整的杭州主题规划中，Agent 会先准备候选 POI，再做 enrich。

### 5.1 链路说明

链路入口在：

- `ActivityPlanningAgent._prepare_theme_poi_candidates()`

整体流程如下：

```text
_prepare_theme_poi_candidates()
→ _resolve_origin_with_amap()            # 若 provider 支持，则补地理起点
→ keyword_seeds_for_theme()              # 生成搜索种子词
→ keyword_expander.expand()              # 扩展搜索关键词
→ local_data_provider.sync_theme_pois()  # 若 provider 支持，则同步主题候选 POI
→ _refresh_runtime_catalog()
→ _enrich_theme_candidates_with_mock_profiles()
→ commerce_provider.merchant_profile() × N
→ repository.upsert_supplies()
```

### 5.2 当前状态

当前项目中这条链路是“可扩展接口 + mock enrich”的模式：

- 如果 `local_data_provider` 实现了 `sync_theme_pois` 或 `amap_client`，就会调用
- 如果没有实现，就优雅跳过
- enrich 阶段使用 `mock_meituan_profile` 补商户画像

这是一种典型的“能力探测式调用”设计。

## 6. 多轮引导链路

当用户不是一次性给出完整需求，而是通过聊天逐步补条件时，走的是 `chat_with_guidance()`。

### 6.1 入口

- `POST /api/chat/guided`

### 6.2 链路

```text
前端
→ /api/chat/guided
→ backend.main.guided_chat()
→ ActivityPlanningAgent.chat_with_guidance()
→ dialogue_manager.process_input()
→ 判断当前状态是否已经具备规划条件
  → 若否：返回下一轮引导问题
  → 若是：调用 ActivityPlanningAgent.plan()
→ repository.save_planning_result()
→ get_conversation_payload()
→ 返回 response + conversation
```

### 6.3 工具位置

这条链路的前半段主要是状态机和请求收集，不直接访问工具。

真正的工具调用仍然在：

- 后续主题候选 enrich
- 刷新阶段
- 预约阶段

## 7. 刷新链路

刷新用于在方案已生成后，对路线、天气、库存做一次校验或估算刷新。

### 7.1 入口

- `POST /api/itineraries/{option_id}/refresh`

### 7.2 调用链路

```text
前端
→ /api/itineraries/{option_id}/refresh
→ backend.main.refresh_itinerary()
→ ActivityPlanningAgent.refresh_itinerary()
→ _latest_planning_or_raise()
→ _find_option()
→ map_provider.route_summary(area_clusters)
→ weather_provider.weather_hint(location_anchor, rainy=weather_sensitive)
→ commerce_provider.check_availability() × N
→ 组装 route / weather / commerce 刷新结果
→ 返回带 tool_events 的刷新响应
```

### 7.3 Provider 与 Tool 的映射

#### 路线刷新

```text
map_provider.route_summary()
→ MockMapDataProvider.route_summary()
→ repository.get_api_cache() / save_api_cache()
→ 返回 ProviderSnapshot
```

#### 天气刷新

```text
weather_provider.weather_hint()
→ MockWeatherProvider.weather_hint()
→ 返回 ProviderSnapshot
```

#### 商户可用性刷新

```text
commerce_provider.check_availability()
→ MockCommerceProvider.check_availability()
→ MockMeituanToolClient.check_availability()
→ 返回 ToolResult + ToolEvent
```

### 7.4 结果特点

刷新接口会显式返回：

- `provider`
- `status`
- `data_confidence`
- `message`
- `tool_events`

这意味着工具调用结果不是被吞掉，而是被结构化透传到上层。

## 8. Provider 同步链路

Provider 同步用于把本地 seed 数据或实时来源同步到当前运行时 catalog。

### 8.1 入口

- `POST /api/providers/sync`

### 8.2 调用链路

```text
前端
→ /api/providers/sync
→ backend.main.sync_providers()
→ ActivityPlanningAgent.sync_provider_data()
→ 若 local_data_provider 实现 sync_live_sources():
    → local_data_provider.sync_live_sources()
    → _refresh_runtime_catalog()
    → list_route_clusters()
    → list_theme_templates()
→ 否则：
    → list_supplies()
    → list_route_clusters()
    → list_theme_templates()
→ 返回同步结果
```

### 8.3 当前设计特点

这条链路也是“有能力就调，没有能力就退回 seed”的设计：

- 支持未来真实 provider 接入
- 目前不阻塞现有演示链路

## 9. 预约草稿链路

这条链路是真正开始频繁调用工具的地方。

### 9.1 入口

- `POST /api/create-booking-draft`

### 9.2 调用链路

```text
前端
→ /api/create-booking-draft
→ backend.main.create_booking_draft()
→ ActivityPlanningAgent.create_booking_draft()
→ _latest_planning_or_raise()
→ _find_option() / get_selected_option()
→ _ensure_experience_card()
→ BookingOrchestrator.create_draft()
→ commerce_provider.check_availability() × N
→ commerce_provider.create_booking_hold()
→ 若 AA 预付：
    → commerce_provider.create_aa_draft()
→ repository.save_booking_draft()
→ 返回 BookingDraft
```

### 9.3 更细的工具层展开

```text
BookingOrchestrator.create_draft()
→ MockCommerceProvider.check_availability()
→ MockMeituanToolClient.check_availability()

→ MockCommerceProvider.create_booking_hold()
→ MockMeituanToolClient.create_booking_hold()

→ MockCommerceProvider.create_aa_draft()
→ MockMeituanToolClient.create_aa_draft()
```

### 9.4 这条链路的特点

- 对每个时间线 item 检查库存
- 汇总成 `BookingDraftItem`
- 生成 `hold_id` 和 `confirm_token`
- 朋友局默认可生成 AA 草稿
- 不直接确认，不做不可逆动作

## 10. 预约确认链路

预约确认是工具链路中最接近“交易确认”的阶段，但仍然保持 mock 安全边界。

### 10.1 入口

- `POST /api/confirm-booking`

### 10.2 调用链路

```text
前端
→ /api/confirm-booking
→ backend.main.confirm_booking()
→ ActivityPlanningAgent.confirm_booking()
→ repository.get_booking_draft()
→ BookingOrchestrator.confirm_draft()
→ commerce_provider.confirm_booking()
→ MockMeituanToolClient.confirm_booking()
→ repository.save_booking_confirmation()
→ 返回 BookingConfirmation
```

### 10.3 工具行为分支

#### 用户不确认

```text
confirm=False
→ BookingOrchestrator.confirm_draft()
→ 直接返回 CANCELLED
→ 不调用 confirm_booking 工具
```

#### 用户确认

```text
confirm=True
→ commerce_provider.confirm_booking()
→ MockMeituanToolClient.confirm_booking()
→ 返回 confirmed / blocked
→ 生成 order_ids / reservation_ids / ticket_ids / hotel_order_ids / delivery_order_ids
```

### 10.4 安全边界

这里体现出项目非常明确的工具边界：

- 工具可以先 hold
- 工具可以生成 draft
- 只有显式确认才进入确认调用
- 即使确认后，当前仍是 mock 订单，不是真实支付

## 11. 反馈收敛链路

反馈本身不是工具调用密集型链路，但它会触发下一轮规划。

### 11.1 入口

- `ActivityPlanningAgent.submit_feedback()`

### 11.2 调用链路

```text
submit_feedback()
→ repository.save_feedback()
→ FeedbackResolver.resolve()
→ ThemePlanner.plan()
→ ItineraryComposer.compose()
→ render_share_card()
→ repository.save_planning_result()
→ repository.save_selected_option()
→ 返回新的 AgentResponse
```

### 11.3 工具位置

这条链路本身不直接调外部工具，属于纯业务重规划。

但它会为后续：

- refresh
- create_booking_draft

重新准备新的路线结果。

## 12. 经验卡链路

除了路线本身，Agent 还会补充体验卡和路线卡。

### 12.1 调用点

主要在：

- `ActivityPlanningAgent._attach_live_context()`
- `ActivityPlanningAgent._ensure_experience_card()`

### 12.2 链路

```text
_attach_live_context()
→ _route_plan_for_option()
→ _ensure_experience_card()
→ experience_card_designer.design()
→ 返回包含 route_plan / experience_card 的 PlanOption
```

这部分不是传统意义上的外部工具调用，但属于“规划结果 enrich 链路”的一部分。

## 13. ToolEvent 回传机制

当前项目对工具调用结果的追踪是比较完整的。

### 13.1 Tool 层生成

在 [mock_meituan.py](file:///d:/meituan%20agent/activity_agent/tools/mock_meituan.py) 中，每次工具调用都通过 `_event()` 生成 `ToolEvent`：

- `name`
- `input_summary`
- `output_summary`
- `status`
- `duration_ms`
- `error`

### 13.2 上层保留

这些 `ToolEvent` 会被：

- `BookingDraft.tool_events`
- `BookingConfirmation.tool_events`
- `AgentResponse.tool_events`
- 刷新接口的 `tool_events`

保留下来

### 13.3 接口层序列化

在 [main.py](file:///d:/meituan%20agent/backend/main.py) 中，`_tool_event_payload()` 会把事件序列化为前端可消费的 JSON。

所以完整链路是：

```text
MockMeituanToolClient
→ ToolResult.event
→ BookingDraft / Confirmation / Response
→ backend.main._tool_event_payload()
→ 前端 JSON 响应
```

## 14. 前后端接口链路总览

从 Web 前端视角看，常用接口与工具调用关系如下：

| 前端接口 | 后端入口 | Agent 方法 | 工具/Provider 调用 |
| --- | --- | --- | --- |
| `/api/chat` | `chat()` | `agent.chat()` | 主要是规划模块；必要时补商户画像 |
| `/api/chat/guided` | `guided_chat()` | `agent.chat_with_guidance()` | 先状态机收集，再走规划 |
| `/api/itineraries/generate` | `generate_itineraries()` | `agent.generate_itineraries()` | 走标准规划链路 |
| `/api/itineraries/{id}/refresh` | `refresh_itinerary()` | `agent.refresh_itinerary()` | map/weather/availability |
| `/api/providers/sync` | `sync_providers()` | `agent.sync_provider_data()` | live source 同步或 seed 回退 |
| `/api/create-booking-draft` | `create_booking_draft()` | `agent.create_booking_draft()` | availability / hold / aa draft |
| `/api/confirm-booking` | `confirm_booking()` | `agent.confirm_booking()` | confirm_booking |

## 15. 当前工具链路的设计特点

总结来看，当前项目的工具调用链路有 5 个明显特点：

### 15.1 Agent 不直接依赖第三方 SDK

所有工具都先通过 provider 或 tool client 封装，避免把第三方能力散落在业务模块中。

### 15.2 规划与交易解耦

规划主链路和预约确认链路分开，避免“生成方案时顺手下单”。

### 15.3 Mock 优先，接口预留

现在主要是：

- 本地 seed 数据
- mock 地图
- mock 天气
- mock commerce

但接口层已经为真实 provider 留好位置。

### 15.4 工具事件全链路可见

工具调用不会被隐藏，而是通过 `ToolEvent` 暴露给上层，便于调试、观测和前端展示。

### 15.5 能力探测式扩展

很多调用采用：

- `getattr(..., "sync_live_sources", None)`
- `getattr(..., "sync_theme_pois", None)`
- `getattr(..., "amap_client", None)`

这种模式允许 provider 能力逐步演进，而不会破坏当前稳定链路。

## 16. 一句话总结

整个 `activity_agent` 的工具调用链路，本质上是一个“接口层 → Agent 编排层 → Provider 适配层 → Tool 执行层”的分层体系：

规划时优先使用本地数据和规则模块，刷新时调用地图/天气/库存 provider，预约时进入 mock commerce 工具链，并通过 `ToolEvent` 将调用过程透明回传给上层接口和前端。
