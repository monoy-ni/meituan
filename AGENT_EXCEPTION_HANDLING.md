# 杭州活动规划 Agent 异常处理机制

## 1. 文档目的

本文档说明整个 `activity_agent` 项目的异常处理机制，重点回答以下问题：

1. 项目中的异常主要来自哪里。
2. 各层分别如何处理异常。
3. 哪些异常会被直接抛出，哪些会被降级吸收。
4. 前后端接口最终如何把异常反馈给调用方。
5. 当前异常处理机制的边界和不足是什么。

这份文档描述的是整个 Agent 的项目级异常处理设计，而不是单个 skill 的错误处理。

## 2. 异常处理的总体原则

整个项目的异常处理遵循 5 条基本原则：

### 2.1 用户输入错误优先显式暴露

像会话不存在、方案不存在、草稿不存在这类问题，不做静默兜底，而是直接抛出明确错误，让调用方知道请求无效。

### 2.2 外部能力失败优先降级

像地图、天气、开放数据、LLM 等外部依赖，如果失败，优先降级到 seed/mock/规则模式，避免主流程整体中断。

### 2.3 不可逆动作必须保守处理

在预约、确认等链路中，系统宁可返回 `blocked`、`cancelled` 或待确认状态，也不会在异常时直接推进不可逆动作。

### 2.4 规划阶段允许“部分不精确”，但不允许“假装成功”

如果真实 provider 不可用，系统会继续给出方案，但会显式标注：

- `degraded`
- `seed`
- `cache`
- `mock`

而不是伪装成实时结果。

### 2.5 对外返回尽量结构化

异常不会只留在日志里，而是尽量转成：

- `HTTPException`
- `status`
- `message`
- `degraded`
- `tool_events`

便于前端和调用方消费。

## 3. 异常来源分类

当前项目中的异常大致可分为 6 类：

1. 输入与状态异常
2. 规划数据异常
3. 外部 Provider 异常
4. LLM 异常
5. 预约与确认异常
6. 存储与序列化异常

下面分别说明。

## 4. 输入与状态异常

这类异常主要表示“请求本身不合法”或“当前状态不满足执行条件”。

### 4.1 会话不存在

在 [agent.py](file:///d:/meituan%20agent/activity_agent/agent.py) 中，`_ensure_session()` 会检查 session 是否存在：

```python
if not self.repository.get_session(session_id):
    raise ValueError(f"Session not found: {session_id}")
```

这类异常出现的典型场景：

- 前端传入了错误的 `session_id`
- 会话还没创建就直接发起 chat/select/booking

### 4.2 当前会话没有规划结果

`_latest_planning_or_raise()` 在没有历史规划结果时会抛错：

```python
raise ValueError(f"No planning result found for session: {session_id}")
```

典型场景：

- 用户还没生成方案就直接刷新、选方案、创建预约草稿

### 4.3 方案不存在

`_find_option()` 找不到 `option_id` 时抛出：

```python
raise ValueError(f"Plan option not found: {option_id}")
```

典型场景：

- 前端传了过期或错误的方案 ID

### 4.4 预约草稿不存在

在 `confirm_booking()` 中，如果拿不到 draft，会抛出：

```python
raise ValueError(f"Booking draft not found: {draft_id}")
```

### 4.5 旧接口参数形式错误

在兼容老接口的 `create_booking_draft(option, request)` 形式中，如果第二个参数不是 `UserRequest`，会直接报错。

### 4.6 接口层处理方式

这些 `ValueError` 在 [main.py](file:///d:/meituan%20agent/backend/main.py) 中通常会被转换成：

- `HTTP 404`

例如：

```python
except ValueError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
```

这说明项目当前把“资源/状态不存在”统一视作一种 404 型业务错误。

## 5. 请求参数校验异常

这类异常主要发生在 FastAPI + Pydantic 层。

### 5.1 Pydantic 模型校验

例如：

- `budget_per_person` 必须 `>= 0`
- `party_size` 必须 `>= 1`
- `route_limit_minutes` 必须 `>= 0`

如果请求体不满足这些约束，FastAPI 会自动返回 `422 Unprocessable Entity`。

### 5.2 当前策略特点

这部分异常不需要业务代码手动处理，因为：

- 校验由框架自动完成
- 调用根本进不到 Agent 逻辑

这属于“接口前置防御”。

## 6. 规划数据异常

这类异常不是接口参数错误，而是“规划过程中无法构造完整结果”。

### 6.1 供给匹配失败

在 [supply_matcher.py](file:///d:/meituan%20agent/activity_agent/modules/supply_matcher.py) 中，`match_slot()` 会先过滤候选供给。

如果严格过滤后没有候选，会放宽条件再找一次：

```python
if not candidates:
    candidates = [ ... 较宽松的候选 ... ]
```

如果放宽之后还是没有候选，才真正抛出：

```python
raise ValueError(f"No supply candidate for slot type {slot.type}")
```

### 6.2 处理策略

这里体现的是“两段式处理”：

1. 先严格匹配
2. 再宽松降级
3. 最后才失败

这是一种典型的规划降级机制。

### 6.3 主题和关系阶段非法值

在合并 LLM 数据时，如果 `scene` 不是合法枚举值，会被捕获并忽略：

```python
try:
    return Scene(str(llm_data["scene"]))
except ValueError:
    return None
```

这说明：

- 非法结构化字段不会直接打断主流程
- 系统优先回退到规则识别结果

## 7. 外部 Provider 异常

这类异常主要发生在真实地图、天气、开放数据接入场景。

### 7.1 ProviderAPIError

在 [live_sources.py](file:///d:/meituan%20agent/activity_agent/providers/live_sources.py) 中定义了：

```python
class ProviderAPIError(Exception):
    """Raised when an external provider responds but cannot be used."""
```

这个异常用于统一承接：

- HTTP 错误
- 超时
- URL 访问错误
- 非 JSON 返回
- 第三方接口业务失败

### 7.2 HTTP JSON 访问层异常

`HTTPJSONClient.get_json()` 内部会把：

- `HTTPError`
- `TimeoutError`
- `URLError`
- `JSONDecodeError`

统一转换成 `ProviderAPIError`。

这意味着：

- 下层网络细节不会直接泄露到业务层
- 上层只需要理解“provider 调用失败”

### 7.3 Amap API 错误处理

`AmapWebServiceClient` 在以下情况下会抛出异常：

- 没有 `AMAP_API_KEY`
- Amap 返回状态不是成功
- route response 不含 `paths`
- weather response 不含 `lives`

### 7.4 Provider 层降级策略

#### 天气 Provider

`AmapWeatherProvider.weather_hint()` 中如果真实接口失败：

- 不继续抛出异常
- 返回 `ProviderSnapshot`
- 状态为 `degraded`
- `data_confidence` 为 `seed`

也就是说：

- 真天气失败不会中断刷新流程
- 只会退回 seed weather hint

#### 地图 Provider

`AmapMapDataProvider.route_summary()` 里如果真实路线失败：

- 捕获 `ProviderAPIError`
- 返回 `degraded + seed`

#### 实时数据同步

`HybridLiveDataProvider.sync_live_sources()` 和 `sync_theme_pois()` 中：

- 每个 provider 的错误会写入 `errors`
- 不会因为单个来源失败就让整个同步失败
- 最终状态可能是：
  - `live_synced`
  - `partially_synced`
  - `degraded_to_seed`
  - `seed_synced`

这是一种“部分成功、整体可用”的异常处理策略。

## 8. LLM 异常

LLM 异常主要定义在 [client.py](file:///d:/meituan%20agent/activity_agent/llm/client.py) 中。

### 8.1 异常类型

```python
class LLMError(RuntimeError):
    pass

class LLMConfigurationError(LLMError):
    pass
```

### 8.2 异常来源

`OpenAICompatibleLLMClient.complete()` 在以下场景会抛异常：

- 未配置 API Key
- 网络请求失败
- 返回 JSON 非法
- 返回结构不符合预期

### 8.3 当前系统策略

项目的初始化策略是：

- 有 API Key：用 `OpenAICompatibleLLMClient`
- 没有 API Key：直接用 `MockLLMClient`

这已经在系统层面规避掉了最常见的配置异常。

### 8.4 协同降级机制

虽然当前部分路径未对运行时 LLM 异常做大范围 try/except 包裹，但整体设计仍然体现了“规则底座 + LLM 增强”原则：

- 没有 LLM 时系统可跑
- LLM 非法结构化值会被忽略
- 规划主链路并不完全依赖 LLM

因此从架构角度看，LLM 是增强能力，不是唯一依赖。

## 9. 定位解析与路线计算中的静默降级

项目中有一类异常处理方式不是“抛错”，而是“静默回退”。

### 9.1 起点定位解析失败

在 `ActivityPlanningAgent._resolve_origin_with_amap()` 中：

- 如果 `amap_client` 不存在，直接返回原 request
- 如果 `resolve_location()` 抛异常，直接返回原 request
- 如果经纬度格式解析失败，直接返回原 request

这是典型的“尽量补充，不阻断主流程”策略。

### 9.2 路线腿计算失败

在构造 route plan 时，如果调用地图 client 的 walking route 失败：

- 会进入 `except Exception`
- 然后退回本地 haversine 距离估算

这说明：

- 实时路线是增强项
- 没有实时路线时，仍可提供一个近似可用结果

## 10. 预约与确认异常

预约链路采用的是“保守推进”策略。

### 10.1 创建预约草稿阶段

在 [booking_orchestrator.py](file:///d:/meituan%20agent/activity_agent/modules/booking_orchestrator.py) 中，`create_draft()` 不会因为个别项目不可用就直接抛错。

它会把每个 item 的可用性写成状态：

- `pending_user_confirmation`
- `unavailable_replace_needed`

也就是说：

- 不可用项目不会直接让整个草稿失败
- 而是进入“需替换”状态交给上层处理

### 10.2 用户未确认

`confirm_draft(confirm=False)` 不抛错，直接返回：

- `ConfirmationStatus.CANCELLED`

这属于业务上的“安全取消”，不是异常。

### 10.3 confirm token 无效

在 mock 工具 `confirm_booking()` 中，如果：

- `hold_id` 为空
- `confirm_token` 非法

不会抛异常，而是返回：

- `status = blocked`
- `reason = missing_or_invalid_confirm_token`

然后上层把它转换成：

- `ConfirmationStatus.BLOCKED`

这说明交易链路优先使用“显式状态失败”，而不是 Python 异常。

### 10.4 设计意义

这种做法很适合预约/交易场景，因为：

- 阻止动作是业务结果，不一定是程序错误
- 对调用方来说，`blocked` 比 500 更可消费

## 11. 存储与序列化异常

项目使用 SQLite 持久化，但当前这一层大多没有显式包裹异常。

### 11.1 当前情况

在 [sqlite_repository.py](file:///d:/meituan%20agent/activity_agent/storage/sqlite_repository.py) 中：

- `sqlite3.connect()`
- SQL 执行
- `json.loads()`
- `json.dumps()`

大多是直接调用，没有单独 try/except 包裹。

### 11.2 这意味着什么

这意味着以下异常如果发生，会直接向上冒泡：

- SQLite 连接失败
- SQL 执行异常
- JSON 反序列化异常
- 数据结构与 dataclass 不匹配

### 11.3 当前架构取舍

项目当前把 repository 视为“基础设施层”，默认认为：

- 本地 SQLite 是稳定可用的
- repository 出错属于严重系统错误

所以这部分不是业务降级，而是系统级失败。

## 12. 接口层异常返回机制

在 [main.py](file:///d:/meituan%20agent/backend/main.py) 中，异常返回主要分三层：

### 12.1 框架自动校验错误

- FastAPI / Pydantic 自动返回 `422`

### 12.2 业务状态错误

像：

- session 不存在
- option 不存在
- draft 不存在

这类 `ValueError` 被转换成：

- `HTTP 404`

### 12.3 未捕获异常

如果发生未处理的异常，例如：

- repository 崩溃
- 代码 bug
- 未覆盖的 runtime error

则会走 FastAPI 默认的：

- `HTTP 500`

这说明项目当前的异常暴露策略是：

- 已知业务异常：显式转换
- 框架输入异常：框架自动处理
- 未知系统异常：保留默认 500

## 13. 降级与异常的关系

这个项目里，很多“异常处理”其实不是 try/except，而是“状态降级”。

常见降级包括：

- 没有 LLM → 使用 `MockLLMClient`
- 没有实时地图/天气 → 使用 mock provider
- 真实 provider 调用失败 → 返回 `degraded_to_seed`
- 严格供给筛选无结果 → 宽松重试
- 路线无法精确计算 → 使用近似估算
- 预约不能确认 → 返回 `blocked` 而不是崩溃

因此整个项目的异常处理机制，可以总结为两条线并行：

1. 真异常：直接抛出并在接口层转换
2. 可恢复失败：转成降级状态继续运行

## 14. 当前机制的优点

### 14.1 用户体验较稳

很多外部依赖失败时，用户仍然能拿到一个可讨论、可调整的方案。

### 14.2 系统边界清晰

会话丢失、方案不存在、草稿不存在等错误不会被悄悄吞掉。

### 14.3 对外部依赖容错较好

地图、天气、开放数据、Amap 路由都已经有明显降级路径。

### 14.4 交易链路安全

确认失败优先转成 `blocked/cancelled` 状态，而不是推进危险动作。

## 15. 当前机制的不足

为了材料完整性，也需要说明当前仍有改进空间。

### 15.1 repository 层缺少统一异常包装

SQLite 和 JSON 相关异常目前大多直接上抛，没有统一的 RepositoryError。

### 15.2 缺少全局异常中间件

FastAPI 目前主要是局部 `try/except ValueError`，尚未定义统一的全局异常处理器。

### 15.3 LLM 运行时异常的统一兜底还不够完整

虽然系统架构上支持“无 LLM 运行”，但若运行时真实 LLM client 抛错，部分高阶链路还可以进一步细化 fallback。

### 15.4 缺少标准化错误码体系

当前更多是：

- `detail`
- `message`
- `status`

还没有统一的：

- `error_code`
- `error_category`
- `retryable`

这对前端精细处理会有一定限制。

## 16. 推荐的后续增强方向

如果后面要继续完善异常处理机制，建议按以下方向演进：

### 16.1 增加统一异常层级

例如：

- `AgentDomainError`
- `RepositoryError`
- `ProviderError`
- `BookingError`
- `ValidationError`

### 16.2 增加全局异常处理器

在 FastAPI 中统一把异常转换成标准响应结构，例如：

```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session not found: sess_xxx",
  "category": "business",
  "retryable": false
}
```

### 16.3 增加可观测性

目前工具调用有 `ToolEvent`，后续可以把异常也纳入统一事件体系，便于：

- 日志追踪
- 接口审计
- 错误分类统计

### 16.4 增加 repository 和序列化层兜底

至少可以在存储层补充：

- SQLite 打开失败说明
- JSON schema 不一致保护
- 数据迁移失败保护

## 17. 一句话总结

整个 `activity_agent` 的异常处理机制，本质上是一套“业务错误显式暴露、外部依赖优先降级、交易动作保守推进、未知系统错误继续上抛”的混合策略：

对可恢复问题，系统尽量退回 seed/mock/规则模式继续服务；对会话、方案、草稿等关键状态错误，则通过明确异常和 HTTP 状态直接反馈给调用方。
