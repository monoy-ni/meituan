# 杭州活动规划 Agent 设计文档

**版本**: v1.4 | **日期**: 2026-06-06

---

## 目录
1. [系统架构](#1-系统架构)
2. [Planning 策略](#2-planning-策略)
3. [工具调用链路](#3-工具调用链路)
4. [异常处理机制](#4-异常处理机制)
5. [数据流程](#5-数据流程)

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Web 前端  │  │  CLI 示例   │  │  SDK 调用  │  │
│  │  (React)  │  │  (demo.py) │  │  (Python)  │
│  └──────┬────┘  └──────┬────┘  └──────┬────┘  │
└─────────┼─────────────────────┼─────────────────────┼─────────┘
          │                     │                     │
┌─────────┴─────────────────────┴─────────────────────┴─────────┐
│                   Agent 层                     │
│  ┌──────────────────────────────────────────────┐      │
│  │      ActivityPlanningAgent (Facade)        │      │
│  │  - chat() / chat_with_guidance()         │      │
│  │  - select_option() / select_and_book()   │      │
│  └───────────────────┬──────────────────────┘      │
└────────────────────┼───────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────┴───────┐  ┌─┴───────────┐  ┌─┴───────────┐
│   业务模块层   │  │  LLM 层  │  │  工具层   │
├───────────────┤  ├────────────┤  ├────────────┤
│ IntentRouter  │  │ OpenAI-   │  │ MockMeituan│
│ ContextCollector│  │ compatible │  │ ToolClient │
│ ThemePlanner    │  │ MockLLM   │  └────────────┘
│ SupplyMatcher  │  └────────────┘
│ ItineraryComposer│
│ FeedbackResolver│
│ BookingOrchestrator│
│ DialogueManager│
└───────────────┘
        │
┌───────┴───────┐
│  ┌───────────────┐
│  │ 数据提供层  │
│  ├───────────┤
│  │ SeedLocal │
│  │ DataProvider│
│  │ MockMap   │
│  │ MockWeather│
│  └───────────┘
└───────────────┘
        │
┌───────┴───────┐
│  ┌───────────────┐
│  │  存储层       │
│  ├───────────────┤
│  │ SQLiteRepository│
│  └───────────────┘
└───────────────┘
```

### 1.2 核心分层

| 层级 | 职责 | 文件位置 |
|------|------|
| Agent 层 | 提供统一 SDK 接口，协调各模块 | `activity_agent/agent.py` |
| 业务模块层 | 意图路由/主题规划/行程编排/反馈处理 | `activity_agent/modules/` |
| LLM 层 | 自然语言理解 | `activity_agent/llm/` |
| 工具层 | 模拟美团 API | `activity_agent/tools/` |
| 数据提供层 | 供给/地图/天气数据 | `activity_agent/providers/` |
| 存储层 | SQLite 持久化 | `activity_agent/storage/` |

---

## 2. Planning 策略

### 2.1 规划流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  1. IntentRouter               │
│  - 识别意图 + 场景               │
│  PLAN/ADJUST/FEEDBACK/BOOKING/REVIEW │
│  FRIENDS/COUPLE                  │
└─────────────────┬───────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  2. ContextCollector           │
│  - 提取结构化请求                 │
│  预算/时间/人数/偏好/约束           │
└─────────────────┬─────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  3. ThemePlanner             │
│  - 匹配杭州主题模板           │
│  6套预设主题                 │
└─────────────────┬─────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  4. SupplyMatcher             │
│  - 按主题槽位匹配供给         │
│  标签匹配 + 预算过滤            │
└─────────────────┬─────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  5. ItineraryComposer       │
│  - 组合成完整行程             │
│  时间线 + 风险提示            │
└─────────────────┬─────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  6. ShareCardGenerator        │
│  - 生成分享卡片/邀约话术       │
└─────────────────────────────────────┘
```

### 2.2 杭州主题策略

| 主题 ID | 名称 | 区域集群 | 适用场景 |
|---------|------|---------|
| hz_old_town_fireworks | 老城烟火半日局 | 河坊街 | 朋友/情侣 |
| hz_canal_citywalk | 运河人文 Citywalk | 桥西 | 朋友/情侣 |
| hz_westlake_easy | 西湖轻松打卡局 | 西湖湖滨 | 朋友/情侣 |
| hz_longwu_suburb | 龙坞茶山近郊局 | 龙坞 | 朋友/情侣 |
| hz_food_tour | 杭州特色美食巡游 | 河坊街 | 朋友/情侣 |
| hz_rainy_indoor | 雨天室内低耗局 | 武林 | 朋友/情侣 |

### 2.3 主题槽位匹配

**朋友局典型槽位**:
```
Activity → Dining → Checkin/Relax

**情侣局典型槽位**:
```
Activity → Dining → Relax → [可选 Gift/Hotel

### 2.4 供给匹配策略

1. **标签匹配**: 计算 `desired_tags ∩ (supply.tags ∪ supply.local_flavor_tags

2. **预算过滤**: supply.price ≤ request.budget_per_person

3. **距离约束**: supply.distance_km ≤ request.travel_radius_km

4. **区域优先**: 优先匹配 area_cluster 一致的供给

5. **去重: 已匹配过的 supply.id 不再重复使用

---

## 3. 工具调用链路

### 3.1 规划链路

```
chat() 调用链路:

ActivityPlanningAgent.chat()
    │
    ├─ repository.add_message() → 保存用户消息
    │
    ├─ intent_router.route() → 意图路由
    │
    ├─ context_collector.collect() → 上下文收集
    │
    ├─ theme_planner.plan() → 主题规划
    │
    ├─ supply_matcher.match_slot() x N → 供给匹配
    │
    ├─ itinerary_composer.compose() → 行程编排
    │
    ├─ share_card_generator.render() x N → 生成分享卡片
    │
    └─ repository.save_planning_result() → 持久化结果
```

### 3.2 预约链路

```
create_booking_draft() 调用链路:

ActivityPlanningAgent.create_booking_draft()
    │
    ├─ repository.get_latest_planning() → 获取最新方案
    │
    ├─ booking_orchestrator.create_draft()
    │   │
    │   ├─ tool_client.check_availability() x N
    │   │   └─ 检查库存可用性
    │   │
    │   ├─ tool_client.create_booking_hold() x N
    │   │   └─ 预约占位
    │   │
    │   ├─ tool_client.create_aa_draft()
    │   │   └─ AA 草稿
    │   │
    │   └─ 返回 BookingDraft
    │
    └─ repository.save_booking_draft() → 持久化草稿
```

### 3.3 确认链路

```
confirm_booking() 调用链路:

ActivityPlanningAgent.confirm_booking()
    │
    ├─ repository.get_booking_draft() → 获取草稿
    │
    ├─ booking_orchestrator.confirm_draft()
    │   │
    │   ├─ tool_client.confirm_booking()
    │   │   └─ 确认预约
    │   │
    │   └─ 返回 BookingConfirmation
    │
    └─ repository.save_booking_confirmation() → 持久化确认
```

### 3.4 对话式链路

```
chat_with_guidance() 调用链路:

ActivityPlanningAgent.chat_with_guidance()
    │
    ├─ repository.add_message()
    │
    ├─ dialogue_manager.process_input()
    │   │
    │   ├─ 状态机状态检查
    │   │
    │   ├─ 需求收集
    │   │
    │   ├─ (状态 READY_TO_PLAN?
    │   │   └─ YES → plan() 规划
    │   │
    │   └─ NO → 返回引导问题
    │
    └─ repository.add_message() → 保存回复
```

---

## 4. 异常处理机制

### 4.1 异常分类

| 类型 | 说明 | 处理策略 |
|------|------|
| **输入异常 | 无效 session_id/option_id/draft_id | 返回 ValueError |
| **数据异常 | 供给匹配失败/无可用供给 | 降级策略 |
| **LLM 异常 | API 超时/限流/错误 | 降级到规则匹配 |
| **工具异常 | Mock API 失败 | 继续执行 |
| **存储异常 | SQLite 错误 | 重试 + 内存 fallback |

### 4.2 LLM 降级策略

```
┌─────────────────────────────────────┐
│          LLM 处理               │
└─────────────┬───────────────────┘
              │
        ┌─────┴─────┐
        │  成功?  │
        └─────┬─────┘
              │ YES
              ▼
    ┌───────────────┐
    │  使用 LLM   │
    │  结果    │
    └───────────────┘
              │ NO
              ▼
    ┌───────────────────┐
    │ 降级到规则匹配    │
    │  IntentRouter   │
    │  ContextCollector│
    └───────────────────┘
```

### 4.3 供给匹配异常处理

| 异常场景 | 处理策略 |
|---------|---------|
| 某槽位无匹配供给 | 跳过可选槽位，扩大标签 |
| 预算不足匹配失败 | 提高预算容差 20% 重试 |
| 区域无供给 | 切换到相邻区域集群 |
| 无可用供给 | 返回空或降级方案 |

### 4.4 预约异常处理

```python
# 伪代码示例
try:
    # 尝试 LLM 理解
    llm_result = llm_client.parse(text)
except (TimeoutError, RateLimitError) as e:
    # 降级到规则
    return rule_based_result = rule_parser(text)
```

### 4.5 安全边界

| 操作 | 安全措施 |
|------|---------|
| create_booking_draft() | 只生成草稿，hold token |
| confirm_booking(confirm=False) | 不产生任何订单 |
| confirm_booking(confirm=True) | 生成 mock 订单 |
| 不可逆操作 | 显式确认 |

---

## 5. 数据流程

### 5.1 数据模型

```
Session (会话)
  ├─ id: str
  ├─ user_id: str
  └─ messages: [Message]

UserRequest (用户请求)
  ├─ scene: Scene
  ├─ budget_per_person: int
  ├─ party_size: int
  ├─ time_window: str
  └─ ...

PlanOption (方案选项)
  ├─ id: str
  ├─ theme_name: str
  ├─ timeline_items: [TimelineItem]
  └─ ...

BookingDraft (预约草稿)
  ├─ items: [BookingDraftItem]
  ├─ hold_id: str
  ├─ confirm_token: str
  └─ ...

BookingConfirmation (预约确认)
  ├─ order_ids: [str]
  ├─ reservation_ids: [str]
  └─ ...
```

### 5.2 数据持久化

```
SQLite 表结构:

sessions
  ├─ id (PK)
  ├─ user_id
  ├─ created_at
  └─ updated_at

messages
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ role (user/assistant)
  └─ content

planning_results
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ request (JSON)
  └─ options (JSON)

booking_drafts
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ hold_id
  ├─ status
  └─ ...

booking_confirmations
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ draft_id (FK)
  └─ ...
```

### 5.3 杭州数据初始化

```
SeedLocalDataProvider.__init__():
  1. 从 supply_catalog.py 加载 SUPPLY_CATALOG
  2. 从 hangzhou_catalog.py 加载 HANGZHOU_ROUTE_CLUSTERS
  3. 从 hangzhou_catalog.py 加载 HANGZHOU_THEME_TEMPLATES
  4. seed 到 SQLite repository
  5. 建立索引优化查询

### 5.4 数据置信度

| 置信度 | 说明 | 来源 |
|--------|------|------|
| seed | 种子数据 | supply_catalog.py |
| cache | 缓存数据 | API 缓存 |
| realtime | 实时数据 | 美团 API (待接入 |

---

## 附录

### A. 关键设计原则

1. **模块化**: 每个模块单一职责
2. **可测试**: 每个模块可独立测试
3. **可替换**: LLM/工具/数据层可替换
4. **可降级**: 规则作为 LLM fallback
5. **安全**: 不可逆操作需确认
6. **可扩展**: 易于添加新城市/新场景

### B. 扩展点

1. 接入真实美团 API
2. 接入高德地图 API
3. 接入真实天气 API
4. 支持更多城市
5. 支持更多场景
6. 支持个性化推荐

---

**文档结束**
