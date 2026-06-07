# 杭州活动规划智能 Agent v1.4

这是一个 Python SDK 真实 MVP，把规则型活动规划核心升级为可持久化、可配置 LLM、可替换工具层的 Agent SDK。支持朋友组局和情侣约会两种场景，杭州本地化数据完整覆盖。

## 核心能力

### 朋友组局
- 活动 → 餐饮 → 放松/夜场 → AA/复盘 完整闭环
- 多方案推荐 + 反馈调整
- 预约草稿 + 确认机制

### 情侣约会
- 关系阶段识别（暧昧/稳定/纪念日）
- 节奏化约会安排
- 礼物/酒店可选
- 回忆沉淀

### 杭州专属
- 8个区域集群（河坊街/西湖/桥西/龙坞等）
- 6套预设主题模板
- 70+本地化供给（景点/餐厅/活动）
- 真实天气/路线提示（mock数据）

## 技术特性

- **LLM 优先**：OpenAI-compatible 接口，负责自然语言理解
- **智能降级**：无 LLM 时自动回退规则匹配
- **SQLite 持久化**：session/消息/方案/选择/反馈/预约/复盘完整记录
- **Mock 工具层**：模拟美团商户搜索、预约检查、AA 草稿等
- **安全边界**：支付/订票/酒店不可逆操作必须显式确认

## 快速开始

### 环境配置

```bash
# 复制配置
cp .env.example .env

# 编辑 .env 设置变量
ACTIVITY_AGENT_LLM_BASE_URL=https://api.openai.com/v1
ACTIVITY_AGENT_LLM_API_KEY=your-api-key
ACTIVITY_AGENT_LLM_MODEL=gpt-4.1-mini
ACTIVITY_AGENT_STORAGE_PATH=./activity_agent.sqlite3
ACTIVITY_AGENT_DATA_MODE=hybrid
ACTIVITY_AGENT_MAP_PROVIDER=amap
AMAP_API_KEY=your-amap-web-service-key
AMAP_CITY=330100
AMAP_POI_KEYWORDS=美食,景点,博物馆,手作,茶馆,酒吧,桌游,密室
HANGZHOU_OPEN_DATA_API_URL=optional-official-dataset-api-url
HANGZHOU_OPEN_DATA_APP_KEY=optional-app-key
HANGZHOU_OPEN_DATA_APP_SECRET=optional-app-secret
HANGZHOU_OPEN_DATA_TOKEN=optional-bearer-token
```

### 运行示例

```bash
# SDK 示例
python demo.py

# 对话式交互
python demo_conversational.py

# LLM 理解演示
python demo_llm_understanding.py

# 运行测试
python -m unittest discover tests
```

### Web 应用

```bash
# Windows 一键启动
start-backend.bat    # 后端：http://localhost:8000
start-frontend.bat   # 前端：http://localhost:3000
```

## SDK 使用示例

```python
from activity_agent import ActivityPlanningAgent
from activity_agent.domain import FeedbackStatus, InviteFeedback

# 初始化 Agent
agent = ActivityPlanningAgent.from_env()
session = agent.start_session(user_id="user_001")

# 聊天规划
response = agent.chat(session.id, "杭州周末不想查攻略，预算人均300")
print(f"推荐方案: {[opt.theme_name for opt in response.options]}")

# 选择方案
agent.select_option(session.id, response.options[0].id)

# 提交朋友反馈
feedback = [
    InviteFeedback("小王", FeedbackStatus.JOIN, budget_feedback=250),
    InviteFeedback("小李", FeedbackStatus.LATE, time_feedback="19:30后到"),
    InviteFeedback("小陈", FeedbackStatus.JOIN, dietary_or_boundary_constraints=["不喝酒"]),
]
revised = agent.submit_feedback(session.id, feedback)

# 创建预约草稿
draft = agent.create_booking_draft(session.id, revised.options[0].id)

# 确认预约
confirmation = agent.confirm_booking(session.id, draft.id, confirm=True)

# 活动复盘
review = agent.create_review(
    session.id,
    actual_cost_per_person=268,
    attendance=4,
    ratings={"河坊街老底子小吃": 4.8, "桥西杭帮菜": 4.6},
)
```

## 对话式交互

新增 `chat_with_guidance()` 接口实现自然对话流程：

```python
agent = ActivityPlanningAgent.from_env()
session = agent.start_session()

# 自动识别群体，多轮收集需求
response1 = agent.chat_with_guidance(session.id, "周末想在杭州找地方玩")
response2 = agent.chat_with_guidance(session.id, "大概人均300左右")
response3 = agent.chat_with_guidance(session.id, "3个人吧，朋友聚会")

# 一键选择+预约
draft, confirmation = agent.select_and_book(session.id, response3.options[0].id)
```

## 目录结构

```
meituan-agent/
├── activity_agent/              # SDK 核心
│   ├── agent.py                # SDK 门面
│   ├── config.py               # 配置管理
│   ├── domain/
│   │   └── models.py          # 数据模型
│   ├── data/
│   │   ├── supply_catalog.py  # 供给数据
│   │   └── hangzhou_catalog.py # 杭州主题/集群
│   ├── modules/               # 业务模块
│   │   ├── intent_router.py   # 意图路由
│   │   ├── context_collector.py # 上下文收集
│   │   ├── theme_planner.py   # 主题规划
│   │   ├── supply_matcher.py  # 供给匹配
│   │   ├── itinerary_composer.py # 行程编排
│   │   ├── feedback_resolver.py # 反馈处理
│   │   ├── booking_orchestrator.py # 预约编排
│   │   ├── dialogue_manager.py # 对话管理
│   │   └── ...
│   ├── providers/             # 数据提供者
│   ├── tools/                 # 工具层
│   ├── storage/               # 存储层
│   └── llm/                   # LLM 层
├── backend/                   # FastAPI 后端
├── frontend/                  # React 前端
├── tests/                     # 单元测试
└── demo*.py                   # 示例脚本
```

## 核心模块

### 1. IntentRouter（意图路由）
识别用户意图（PLAN/ADJUST/FEEDBACK/BOOKING/REVIEW）和场景（FRIENDS/COUPLE）

### 2. ContextCollector（上下文收集）
从自然语言提取预算、时间、人数、偏好等结构化请求

### 3. ThemePlanner（主题规划）
根据场景和偏好匹配合适的杭州本地化主题

### 4. SupplyMatcher（供给匹配）
从杭州供给库中匹配符合主题槽位的商户

### 5. ItineraryComposer（行程编排）
将匹配的供给组合成完整行程方案

### 6. FeedbackResolver（反馈处理）
根据朋友/参与者反馈调整方案

### 7. BookingOrchestrator（预约编排）
创建预约草稿、确认预约（mock 实现）

## 杭州数据

| 类型 | 数量 | 说明 |
|------|------|------|
| 区域集群 | 8 | 河坊街/西湖/桥西/龙坞/湘湖等 |
| 主题模板 | 6 | 老城烟火/运河Citywalk/西湖轻松/龙坞近郊/美食巡游/雨天室内 |
| 供给数据 | 70+ | 景点/餐厅/活动/放松/打卡点 |

详细数据说明见 [data_folder_explanation.md](./data_folder_explanation.md)

## 安全边界

- `create_booking_draft()` 只生成草稿和 hold token
- `confirm_booking(..., confirm=False)` 不产生订单
- 只有显式 `confirm=True` 才返回 mock 订单ID
- Mock 层不做真实支付/出票/酒店下单

## 设计文档

详细设计文档见 [DESIGN.md](./DESIGN.md)，包含：
- Planning 策略
- 工具调用链路
- 异常处理机制
- 系统架构
- 数据流程

## API 文档

启动后端后访问 http://localhost:8000/docs 查看完整 OpenAPI 文档。

## 公共接口

```python
ActivityPlanningAgent.from_env()
agent.start_session(user_id: str | None = None) -> Session
agent.chat(session_id: str, text: str) -> AgentResponse
agent.chat_with_guidance(session_id: str, text: str) -> AgentResponse
agent.select_option(session_id: str, option_id: str) -> AgentResponse
agent.submit_feedback(session_id: str, feedback: list[InviteFeedback]) -> AgentResponse
agent.select_and_book(session_id: str, option_id: str) -> tuple[BookingDraft, BookingConfirmation]
agent.create_booking_draft(...) -> BookingDraft
agent.confirm_booking(...) -> BookingConfirmation
agent.create_review(...) -> AfterActionReview
```

## 许可证

MIT
