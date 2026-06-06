# 活动规划组局 Agent v1

这是一个 Python SDK 真实 MVP，不只是 demo。它把当前规则型活动规划核心升级为可持久化、可配置 LLM、可替换工具层的 Agent SDK。

首版能力：

- 朋友组局：活动 → 餐饮 → 放松/夜场 → AA/复盘。
- 情侣约会：关系阶段识别 → 节奏化约会 → 礼物/酒店可选 → 回忆沉淀。
- LLM 使用 OpenAI-compatible 配置，负责自然语言理解和结构化提取。
- 当前规则模块继续作为安全底座和 LLM 降级路径。
- SQLite 持久化 session、消息、方案、选择、反馈、预约草稿、确认记录和复盘。
- Mock 美团工具模拟商户搜索、可预约检查、预约 hold、AA 草稿、酒店/票券/小时达草稿和确认预约。
- 所有支付、订票、酒店、不可逆预约都必须显式确认；确认前只生成草稿。

## 配置

复制 `.env.example` 后设置环境变量，或在运行前直接设置：

```bash
ACTIVITY_AGENT_LLM_BASE_URL=https://api.openai.com/v1
ACTIVITY_AGENT_LLM_API_KEY=
ACTIVITY_AGENT_LLM_MODEL=gpt-4.1-mini
ACTIVITY_AGENT_LLM_TEMPERATURE=0.2
ACTIVITY_AGENT_LLM_TIMEOUT_SECONDS=20
ACTIVITY_AGENT_STORAGE_PATH=./activity_agent.sqlite3
ACTIVITY_AGENT_TOOL_MODE=mock
```

如果没有 `ACTIVITY_AGENT_LLM_API_KEY`，SDK 会使用 `MockLLMClient`，仍然可以完整跑通本地 MVP 闭环。

## 快速运行

```bash
python demo.py
python -m unittest
```

## SDK 使用示例

```python
from activity_agent import ActivityPlanningAgent
from activity_agent.domain import FeedbackStatus, InviteFeedback

agent = ActivityPlanningAgent.from_env()
session = agent.start_session(user_id="u1")

response = agent.chat(session.id, "今晚有点无聊，想叫朋友出来，预算人均200，别太远")
print(response.share_cards[0])

agent.select_option(session.id, response.options[0].id)

feedback = [
    InviteFeedback("小王", FeedbackStatus.JOIN, budget_feedback=180),
    InviteFeedback("小李", FeedbackStatus.LATE, time_feedback="20:30后到"),
    InviteFeedback("小陈", FeedbackStatus.JOIN, dietary_or_boundary_constraints=["不喝酒"]),
]
revised = agent.submit_feedback(session.id, feedback)

draft = agent.create_booking_draft(session.id, revised.options[0].id)
confirmation = agent.confirm_booking(session.id, draft.id, confirm=True)

review = agent.create_review(
    session.id,
    actual_cost_per_person=166,
    attendance=4,
    ratings={revised.options[0].timeline_items[1].merchant_name: 4.8},
)
```

## 公共接口

- `ActivityPlanningAgent.from_env()`
- `agent.start_session(user_id: str | None = None) -> Session`
- `agent.chat(session_id: str, text: str) -> AgentResponse`
- `agent.select_option(session_id: str, option_id: str) -> AgentResponse`
- `agent.submit_feedback(session_id: str, feedback: list[InviteFeedback]) -> AgentResponse`
- `agent.create_booking_draft(session_id: str, option_id: str, pay_mode: PayMode | None = None) -> BookingDraft`
- `agent.confirm_booking(session_id: str, draft_id: str, confirm: bool) -> BookingConfirmation`
- `agent.create_review(session_id: str, actual_cost_per_person: int, attendance: int, ratings: dict, complaints: list[str] | None = None) -> AfterActionReview`

为兼容早期测试，仍保留：

- `agent.plan(text)`
- `agent.render_share_card(option, request)`
- `agent.create_booking_draft(option, request)`
- `agent.create_review(option, actual_cost_per_person, attendance, ratings)`

## 目录结构

```text
activity_agent/
  agent.py                         # SDK facade
  config.py                        # LLM / storage / tool settings
  domain/models.py                 # dataclass + enum 数据对象
  data/supply_catalog.py           # mock 本地供给
  llm/
    client.py                      # OpenAI-compatible + Mock LLM clients
    orchestrator.py                # LLM JSON understanding layer
  tools/
    mock_meituan.py                # mock 美团工具 API
  storage/
    sqlite_repository.py           # SQLite persistence
  modules/
    intent_router.py
    context_collector.py
    theme_planner.py
    supply_matcher.py
    itinerary_composer.py
    share_card_generator.py
    feedback_resolver.py
    booking_orchestrator.py
    review_memory.py
tests/
  test_activity_agent.py           # 原核心回归测试
  test_mvp_sdk.py                  # SDK / LLM / SQLite / mock 工具测试
```

## 安全边界

- `create_booking_draft()` 只生成 `pending_user_confirmation` 草稿、hold 和 confirm token。
- `confirm_booking(..., confirm=False)` 不会产生任何 mock 订单。
- 只有 `confirm_booking(..., confirm=True)` 才会返回 mock order/reservation/ticket/hotel/delivery ids。
- Mock 工具层不做真实支付、真实出票、真实酒店下单或真实配送。

