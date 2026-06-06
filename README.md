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

## 对话式交互（新功能）

新增 `chat_with_guidance()` 接口实现完整的对话式流程：

1. **自动识别群体** - 通过对话内容判断是朋友局还是约会
2. **多轮引导收集需求** - 自然地逐步询问预算、时间、氛围等
3. **智能关系推断** - 情侣场景不直接问关系阶段，通过对话推断
   - "怕尴尬" → 暧昧/追求中
   - "纪念日" → 纪念日模式
   - "老夫老妻" → 稳定情侣
4. **多方案推荐** - 收集完需求后生成 3 个方案
5. **一键预约** - `select_and_book()` 自动完成选择到下单

### LLM 智能理解（升级）

不再依赖硬编码关键字匹配，改用 LLM 进行自然语言理解：

- **LLM 优先** - 有 API Key 时使用 OpenAI 兼容的 LLM 深度理解
- **智能降级** - 没有 LLM 时自动回退到规则匹配
- **置信度评估** - 对理解结果给出置信度，把握不大时会确认
- **上下文感知** - 结合历史对话理解当前意图

运行对话式演示：
```bash
python demo_conversational.py
python demo_llm_understanding.py  # 查看 LLM 理解能力
```

## Web 前端应用

我们提供了完整的 React 前端界面，让你可以通过浏览器与智能 Agent 交互！

### 项目结构
```
meituan-agent/
├── backend/              # FastAPI 后端
│   ├── main.py          # API 服务
│   └── requirements.txt # Python 依赖
└── frontend/            # React 前端
    ├── src/
    │   ├── components/  # React 组件
    │   ├── App.js      # 主应用
    │   └── api.js      # API 调用
    └── package.json    # Node 依赖
```

### 快速启动

#### Windows 用户
1. 启动后端服务（需要新的终端窗口）：
```cmd
start-backend.bat
```

2. 启动前端服务（需要另一个终端窗口）：
```cmd
start-frontend.bat
```

#### 手动启动

**1. 启动后端：**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
后端将运行在 http://localhost:8000

**2. 启动前端：**
```bash
cd frontend
npm install
npm start
```
前端将运行在 http://localhost:3000

### 功能特点
- 💬 多轮对话界面 - 自然语言交互
- 🎨 活动方案展示 - 美观的卡片布局
- 📋 预约流程 - 从选择到确认的完整流程
- 📱 响应式设计 - 支持手机和桌面端
- 🔄 实时交互 - 流畅的用户体验

### API 文档
启动后端后，访问 http://localhost:8000/docs 查看完整的 API 文档。

