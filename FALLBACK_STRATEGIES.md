# 活动规划 Agent 降级策略清单

本文档完整记录项目中所有的降级机制、回退策略和容错方案，便于审查和移除冗余策略。

---

## 一、LLM 理解降级

### 1.1 LLM 客户端选择降级
**位置**：`activity_agent/agent.py:54-64`
**触发条件**：未配置 `ACTIVITY_AGENT_LLM_API_KEY`
**生效逻辑**：
```python
self.llm_client = llm_client or (
    OpenAICompatibleLLMClient(self.settings.llm) if self.settings.llm.api_key else MockLLMClient()
)
```
**用户体验影响**：
- ✅ 正常工作，使用离线规则解析
- ⚠️ 理解能力较弱，仅支持关键字匹配

---

### 1.2 LLM Orchestrator 异常降级
**位置**：`activity_agent/llm/orchestrator.py:38-60`
**触发条件**：
- LLM API 调用失败
- LLM 返回非 JSON 格式
- JSON 解析错误
**生效逻辑**：
```python
try:
    raw = self.client.complete(messages)
    data = json.loads(raw)
    # ... 正常处理
except Exception as exc:
    # 降级：返回空数据 + degraded 标志
    return LLMUnderstanding(data={}, degraded=True, event=error_event)
```
**用户体验影响**：
- ⚠️ `degraded=True` 标记在响应中
- ✅ 系统继续使用规则解析（在 ContextCollector 中）

---

### 1.3 DialogueManager LLM 理解降级（双重降级）
**位置**：`activity_agent/modules/dialogue_manager.py:71-214`
**触发条件**：
1. LLM 不可用（已降级到 MockLLMClient）
2. LLM 返回置信度 < 0.3
3. LLM 调用抛出异常
**生效逻辑**：
```python
def _understand(self, text, history):
    if self._use_llm:
        try:
            understanding = self._understand_with_llm(text, history)
            if understanding.confidence >= 0.3:
                return understanding  # LLM 结果可用
        except Exception:
            pass
    # 降级：使用规则解析
    return self._understand_with_rules(text)
```
**两个理解层对比**：
| 层级 | 位置 | 触发条件 | 降级目标 |
|------|------|----------|----------|
| L1 | `llm/orchestrator.py` | LLM API 失败 | `degraded=True` 标志，空数据 |
| L2 | `modules/dialogue_manager.py` | 置信度低或异常 | 切换到规则解析 |

**冗余分析**：⚠️ L1 和 L2 存在功能重叠，可能需要合并

---

## 二、用户需求解析降级

### 2.1 LLM 数据解析安全降级
**位置**：`activity_agent/agent.py:273-299`
**触发条件**：
- 字段类型转换失败
- 字段值不存在
**生效逻辑**：
```python
def _safe_int(self, value, fallback):
    try:
        return int(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback
```
**用户体验影响**：
- ✅ 使用安全默认值，不会崩溃
- ⚠️ 可能丢失部分用户输入

---

### 2.2 LLM 场景识别降级
**位置**：`activity_agent/agent.py:264-271`
**触发条件**：LLM 返回的 `scene` 字段无效或不存在
**生效逻辑**：
```python
def _scene_from_llm(self, llm_data):
    if not llm_data or not llm_data.get("scene"):
        return None  # 降级：不使用 LLM 场景信息
    try:
        return Scene(str(llm_data["scene"]))
    except ValueError:
        return None  # 降级：无效场景值
```
**用户体验影响**：
- ✅ 后续使用 IntentRouter 重新判断场景
- ⚠️ 可能增加用户确认轮次

---

### 2.3 ContextCollector 默认值降级（多维度）
**位置**：`activity_agent/modules/context_collector.py:152-185`
**触发条件**：用户未提供某个维度信息
**生效逻辑**：

#### 2.3.1 时间窗口降级
```python
time_window=(partial_request.time_window if partial_request else None)
or _parse_time_window(normalized, scene)
or ("weekend 15:00-22:30" if scene == Scene.COUPLE else "today 18:30-23:30")
```
**默认值**：
- 情侣：周末 15:00-22:30
- 朋友：今天 18:30-23:30

#### 2.3.2 位置降级
```python
location_anchor=(partial_request.location_anchor if partial_request else None)
or _parse_location(normalized)
or "current_location"
```
**默认值**：`current_location`（当前位置 3km 内）

#### 2.3.3 预算降级
```python
budget_per_person=(partial_request.budget_per_person if partial_request else None)
or parsed_budget
or default_budget  # 情侣 360，朋友 220
```
**降级预算调整**：
```python
if constraints["cheaper"] and parsed_budget is None and not partial_request:
    default_budget = 260 if scene == Scene.COUPLE else 150  # 降价模式
```

#### 2.3.4 人数降级
```python
party_size=(partial_request.party_size if partial_request else None)
or _parse_party_size(normalized, scene)
or (2 if scene == Scene.COUPLE else 4)
```
**默认值**：
- 情侣：2 人
- 朋友：4 人

#### 2.3.5 关系阶段降级（情侣场景）
```python
relationship_stage=(partial_request.relationship_stage if partial_request else None)
or ("稳定情侣" if scene == Scene.COUPLE else None)
```
**默认值**：稳定情侣

#### 2.3.6 关系目标降级（情侣场景）
```python
relationship_goal=(partial_request.relationship_goal if partial_request else None)
or ("创造共同体验" if scene == Scene.COUPLE else None)
```
**默认值**：创造共同体验

#### 2.3.7 Mood Tags 降级
```python
if scene == Scene.FRIENDS and not request.mood_tags:
    request = replace(request, mood_tags=["新鲜", "低耗社交"])
if scene == Scene.COUPLE and not request.mood_tags:
    fallback_moods = ["轻互动", "安全"] if request.relationship_stage == "暧昧/追求中" else ["浪漫", "保鲜"]
    request = replace(request, mood_tags=fallback_moods)
```
**默认值**：
- 朋友：新鲜、低耗社交
- 暧昧情侣：轻互动、安全
- 其他情侣：浪漫、保鲜

**用户体验影响**：
- ✅ 即使信息不全也能生成方案
- ⚠️ 通过 `assumptions` 字段告知用户使用了默认值
- ⚠️ 通过 `missing_questions` 字段询问缺失信息

---

### 2.4 LLM 数据与规则解析的混合降级
**位置**：`activity_agent/agent.py:273-299`
**触发条件**：LLM 返回数据 + 规则解析同时存在
**生效逻辑**：
```python
# LLM 数据与现有数据合并
hard_constraints = {**request.hard_constraints, **data.get("hard_constraints", {})}
mood_tags = [*request.mood_tags, *data.get("mood_tags", [])]
```
**冗余分析**：⚠️ LLM 降级标记 `degraded=True` 实际未被使用，最终都会走规则解析

---

## 三、功能降级（双重路径）

### 3.1 对话路径降级（chat vs chat_with_guidance）
**位置**：
- `chat()`：原始直接路径
- `chat_with_guidance()`：新增对话式路径
**触发条件**：开发者选择使用哪个接口
**生效逻辑**：
```python
# 路径 A：无对话管理
agent.chat(session_id, text)

# 路径 B：有对话管理
agent.chat_with_guidance(session_id, text)
```
**功能对比**：
| 特性 | chat() | chat_with_guidance() |
|------|--------|----------------------|
| 对话状态管理 | ❌ 无 | ✅ 有 |
| 逐步收集需求 | ❌ 一次性 | ✅ 多轮对话 |
| 降级策略 | LLM → 规则 | LLM → 规则 → 追问 |
**冗余分析**：⚠️ 两个路径功能重叠，可考虑统一

---

### 3.2 数据来源降级（LLM 数据与规则解析）
**位置**：`activity_agent/agent.py:264-299` + `context_collector.py`
**生效逻辑**：
```python
# 步骤 1：尝试从 LLM 获取数据
understanding = self.llm_orchestrator.understand(text, history)

# 步骤 2：使用规则解析（忽略 LLM 的 degraded 标记）
request, missing, assumptions = self.context_collector.collect(route, text, partial_request)

# 步骤 3：尝试合并 LLM 数据（如果可用）
request = self._merge_llm_data(request, understanding.data or {})
```
**冗余分析**：
- ⚠️ LLM 降级标记 `degraded=True` 不影响流程
- ⚠️ 规则解析总是运行，LLM 数据仅作为补充
- ❓ 是否需要保留 LLM 理解层？

---

## 四、数据持久化降级

### 4.1 存储路径默认降级
**位置**：`activity_agent/config.py:25-32`
**触发条件**：未配置 `ACTIVITY_AGENT_STORAGE_PATH`
**生效逻辑**：
```python
@dataclass(frozen=True)
class StorageSettings:
    path: str = "./activity_agent.sqlite3"  # 默认值

    @classmethod
    def from_env(cls):
        return cls(path=os.getenv("ACTIVITY_AGENT_STORAGE_PATH", cls.path))
```

---

### 4.2 内存存储降级选项
**位置**：`activity_agent/agent.py:51`
**触发条件**：初始化时传入特殊路径 `:memory:`
**生效逻辑**：
```python
# 初始化时可配置为内存存储
agent = ActivityPlanningAgent(settings=AgentSettings(
    storage=StorageSettings(path=":memory:")
))
```
**用户体验影响**：
- ⚠️ 进程退出后数据丢失
- ✅ 适合测试场景

---

## 五、前端降级策略

### 5.1 API 调用失败降级
**位置**：`frontend/src/App.js`
**触发条件**：任何 API 调用抛出异常
**生效逻辑**：
```javascript
try {
    const response = await sendChatMessage(sessionId, inputText);
    // 正常处理
} catch (error) {
    console.error('发送消息失败:', error);
    // 降级：静默失败，仅记录日志
} finally {
    setIsLoading(false);
}
```
**用户体验影响**：
- ⚠️ 用户看不到错误提示
- ⚠️ 可能导致界面状态不一致
- ❌ 缺少友好的错误处理和重试机制

---

### 5.2 会话初始化降级
**位置**：`frontend/src/App.js:33-45`
**触发条件**：`createSession()` API 调用失败
**生效逻辑**：
```javascript
const initSession = async () => {
    try {
        const data = await createSession();
        setSessionId(data.session_id);
    } catch (error) {
        console.error('初始化会话失败:', error);
        // 降级：无后续处理，sessionId 保持 null
    }
};
```
**用户体验影响**：
- ⚠️ 用户可以打开界面但无法使用
- ❌ 缺少错误提示和重试按钮

---

### 5.3 数据安全访问降级
**位置**：`frontend/src/App.js`
**触发条件**：可选字段可能为 undefined
**生效逻辑**：
```javascript
// 使用可选链和默认值
if (response.options && response.options.length > 0) {
    setOptions(response.options);
} else {
    setOptions([]);  // 降级到空数组
}

const isSelected = selectedOption?.id === option.id;  // 可选链
```

---

## 六、业务流程降级

### 6.1 预约流程降级（模拟）
**位置**：`activity_agent/tools/mock_meituan.py`
**触发条件**：所有真实 API 调用都降级到模拟
**生效逻辑**：MockMeituanToolClient 模拟所有操作

| 操作 | 模拟行为 |
|------|----------|
| 搜索商户 | 返回本地数据 |
| 可用性检查 | 总是可用 |
| 创建预约 Hold | 生成 UUID，立即过期 |
| 确认预约 | 生成模拟订单 ID |

**用户体验影响**：
- ✅ 完整流程演示
- ⚠️ 无真实支付、预约
- ⚠️ 安全提示："半自动确认模式"

---

### 6.2 朋友反馈收敛降级
**位置**：`activity_agent/modules/feedback_resolver.py`
**触发条件**：用户反馈与原始方案有冲突
**生效逻辑**：
- 调整预算到最低可接受值
- 应用约束条件（不喝酒、室内等）
- 重新生成方案

---

## 七、冗余策略总结与建议

### 7.1 立即可以移除的冗余

| 策略 | 位置 | 原因 | 建议 |
|------|------|------|------|
| LLM Orchestrator 降级标记 | `llm/orchestrator.py:50` | `degraded=True` 不影响后续流程 | 移除或实际使用 |
| 旧 `chat()` 接口保留 | `agent.py:80-106` | 已有新的 `chat_with_guidance()` | 标记为 deprecated 并逐步迁移 |

---

### 7.2 考虑合并的重复降级

| 重复项 | 描述 | 建议 |
|--------|------|------|
| LLM 理解降级层 | L1 (orchestrator) 和 L2 (dialogue_manager) 重复 | 合并为一层 |
| 需求解析逻辑 | `context_collector.py` 与 `dialogue_manager.py` 都有关键字匹配 | 统一解析逻辑 |

---

### 7.3 需要补充的降级（当前缺失）

| 场景 | 当前处理 | 建议补充 |
|------|----------|----------|
| 前端 API 错误 | 仅 console.error | 用户友好提示 + 重试按钮 |
| 后端会话丢失 | 会抛出异常 | 创建新会话 + 提示用户 |
| SQLite 数据库错误 | 异常会传播 | 降级到内存存储 + 告警 |
| 方案生成失败 | 异常会传播 | 返回友好提示 + 引导重新开始 |

---

## 八、降级决策树

```
用户输入
   │
   ├─▶ DialogueManager._understand()
   │      │
   │      ├─ LLM 可用？ ──是──▶ confidence >= 0.3？ ──是──▶ 使用 LLM 结果
   │      │      │                           │
   │      │      否                          否
   │      │      │                           │
   │      └───▶ 使用规则解析 ─────────────────┘
   │
   ├─▶ ContextCollector.collect()
   │      │
   │      ├─ 解析时间？ ──否──▶ 默认值
   │      ├─ 解析位置？ ──否──▶ 默认值
   │      ├─ 解析预算？ ──否──▶ 默认值
   │      ├─ 解析人数？ ──否──▶ 默认值
   │      └─ ... 其他字段
   │
   ├─▶ Plan 生成
   │      │
   │      └─ 使用默认商户数据（supply_catalog.py）
   │
   └─▶ 持久化
          │
          └─ SQLite 错误？ ──是──▶ 异常传播（无降级）
```

---

## 九、测试覆盖检查

| 降级场景 | 是否有测试 | 测试文件 |
|----------|-----------|---------|
| LLM 失败降级 | ✅ 有 | `test_mvp_sdk.py:54-68` |
| MockLLMClient 行为 | ✅ 有 | 多处间接测试 |
| 前端错误处理 | ❌ 无 | - |

---

**文档生成时间**：2026-06-06
**代码版本**：基于当前仓库状态分析
