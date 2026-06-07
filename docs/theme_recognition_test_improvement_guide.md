# 主题辨别系统测试与改进指南

## 📋 目录

1. [概述](#概述)
2. [系统架构分析](#系统架构分析)
3. [完整测试流程](#完整测试流程)
4. [结果分析与问题定位](#结果分析与问题定位)
5. [代码改进指南](#代码改进指南)
6. [扩展新主题](#扩展新主题)
7. [完整示例](#完整示例)

---

## 📖 概述

### 主题辨别系统组成

| 模块 | 文件 | 职责 |
|------|------|------|
| **理解层** | `activity_agent/modules/dialogue_manager.py` | 用户需求理解（LLM + 规则） |
| **规划层** | `activity_agent/modules/theme_planner.py` | 主题选择与排序 |
| **数据层** | `activity_agent/data/theme_keyword_seeds.py` | 主题关键词定义 |

### 当前测试覆盖

| 测试类型 | 文件 | 状态 |
|----------|------|------|
| 主题确认验证 | `tests/theme_confirmation_harness.py` | ✅ 已完成 |
| 测试用例集 | `tests/theme_confirmation_cases.py` | ✅ 已完成 |
| 快速运行 | `tests/run_mock_theme_confirmation.py` | ✅ 已完成 |

---

## 🏗️ 系统架构分析

### 1. 用户需求理解 - `DialogueManager`

**核心代码流程**:
```
用户输入
  ↓
DialogueManager._understand()
  ├─→ DialogueManager._understand_with_llm()  [尝试 LLM]
  └─→ DialogueManager._understand_with_rules() [规则降级]
  ↓
UserUnderstanding 对象
  ├─ scene: friends/couple
  ├─ relationship_stage
  ├─ mood_tags
  └─ constraints
```

**关键方法位置**: `activity_agent/modules/dialogue_manager.py`

```python
# 第 77-98 行
def _understand(self, text: str, history, scene_hint):
    """统一理解入口：尝试 LLM -> 失败则回退规则"""

# 第 100-163 行
def _understand_with_llm(self, text: str, history):
    """使用 LLM 深度理解"""

# 第 165-300+ 行
def _understand_with_rules(self, text: str, scene_hint):
    """规则解析"""
```

---

### 2. 主题选择与评分 - `ThemePlanner`

**核心代码流程**:
```
UserRequest
  ↓
ThemePlanner.plan()
  ├─→ _is_hangzhou_day_out()?  [判断是否杭州主题]
  │   ├─ YES → _score_hangzhou()
  │   └─ NO
  ├─→ scene == couple?
  │   ├─ YES → _score_couple()
  │   └─ NO → _score_friends()
  ↓
Top 3 主题列表
```

**关键方法位置**: `activity_agent/modules/theme_planner.py`

```python
# 第 251-259 行
def plan(self, request: UserRequest) -> list[Theme]:
    """主题规划主入口"""

# 第 261-275 行
def _is_hangzhou_day_out(self, request: UserRequest) -> bool:
    """判断是否是杭州相关主题"""

# 第 277-291 行
def _score_hangzhou(self, theme: Theme, request: UserRequest) -> int:
    """杭州主题评分"""

# 第 293-301 行
def _score_friends(self, theme: Theme, request: UserRequest) -> int:
    """朋友主题评分"""

# 第 303-314 行
def _score_couple(self, theme: Theme, request: UserRequest) -> int:
    """情侣主题评分"""
```

---

## 🧪 完整测试流程

### 第一步：运行测试框架

使用 Mock LLM 模式快速验证（推荐）：

```bash
# 方式 1：Mock 模式快速运行（推荐）
python -m tests.run_mock_theme_confirmation

# 方式 2：完整模式（需要 LLM API Key）
python -m tests.run_theme_confirmation_validation

# 方式 3：unittest 集成
python -m unittest tests.test_theme_confirmation_validation
```

---

### 第二步：查看测试报告

测试完成后，报告位置在：
```
reports/theme_confirmation_report.md   # Markdown 格式（易读）
reports/theme_confirmation_report.json  # JSON 格式（程序处理）
```

**报告关键指标**:
- `total_cases`: 总用例数
- `case_pass_rate`: 用例通过率
- `theme_accuracy`: 主题定位准确率
- `relationship_stage_accuracy`: 关系阶段准确率

---

### 第三步：自定义测试用例

编辑文件: `tests/theme_confirmation_cases.py`

```python
# 添加新测试用例
ThemeConfirmationCase(
    case_id="my_test_001",
    title="测试特定场景",
    category="自定义测试",
    description="详细描述这个用例的测试目的",
    turns=[
        ThemeConfirmationTurn(message="用户输入", scene_hint=Scene.FRIENDS),
    ],
    expected_scene=Scene.FRIENDS,
    expected_relationship_stage=None,
    expected_top_theme_key="friends_recovery",
    expected_final_state="awaiting_selection",
    min_options=3,
    notes="备注信息",
),
```

---

## 🔍 结果分析与问题定位

### 常见问题模式

| 问题类型 | 可能原因 | 解决方案位置 |
|----------|----------|--------------|
| **场景识别错误** (friends ↔ couple) | 关键词不足或不匹配 | `dialogue_manager.py` `_understand_with_rules()` |
| **杭州主题识别错误** | 杭州触发标签不完整 | `theme_planner.py` `_is_hangzhou_day_out()` |
| **主题评分不准确** | 评分权重或标签匹配问题 | `theme_planner.py` `_score_*()` 方法 |
| **主题完全不匹配** | 主题标签或数据缺失 | `theme_planner.py` 主题定义区域 |
| **LLM 理解错误** | Prompt 效果不好 | `dialogue_manager.py` `_understand_with_llm()` |

---

### 问题定位步骤

#### 1️⃣ 场景识别问题

**问题**: 用户说"约会"但识别为朋友

**检查清单**:
1. 打开 `activity_agent/modules/dialogue_manager.py`
2. 检查 `_understand_with_rules()` 方法中的关键词 (第 171-192 行)
3. 确认关键词是否包含目标词汇

**常见问题点**:
```python
# 第 171-192 行附近
couple_keywords = [
    "情侣",
    "约会",  # 确保有这个关键词！
    ...
]
```

---

#### 2️⃣ 杭州主题识别问题

**问题**: 用户提到"西湖"但没有推荐杭州主题

**检查清单**:
1. 打开 `activity_agent/modules/theme_planner.py`
2. 检查 `_is_hangzhou_day_out()` 方法 (第 261-275 行)
3. 确认 `city_tags` 集合包含目标词汇

**常见问题点**:
```python
# 第 262-274 行
city_tags = {
    "杭州",
    "西湖",  # 确保有这个标签！
    ...
}
```

---

#### 3️⃣ 主题评分不准确

**问题**: 正确的主题没有排在第一位

**检查清单**:
1. 查看 `_score_hangzhou()`、`_score_friends()`、`_score_couple()` 方法
2. 检查评分权重设置
3. 确认标签匹配逻辑

**评分逻辑示例**:
```python
# 朋友主题评分 (第 293-301 行)
def _score_friends(self, theme: Theme, request: UserRequest) -> int:
    score = 3 * len(set(theme.trigger_tags) & set(request.mood_tags))
    # 调整系数：3 太低？改成 5？
    ...
```

---

## 🛠️ 代码改进指南

### 改进 1: 增强关键词匹配

**目标**: 提高 `DialogueManager` 规则匹配准确率

**文件**: `activity_agent/modules/dialogue_manager.py`

**代码位置**: 第 165 行左右 `_understand_with_rules()` 方法

**改进步骤**:

1. **扩展关键词列表**
```python
# 在 _understand_with_rules() 中
friends_keywords = [
    "朋友", "朋友局", "聚聚", "局", "哥们", "姐妹", "同事", "大家", "几个人",
    "兄弟", "闺蜜", "伙伴", "聚会", "团建", "聚餐"  # 新增关键词
]

couple_keywords = [
    "情侣", "情侣约会", "约会", "对象", "女朋友", "男朋友",
    "老婆", "老公", "另一半", "ta", "两个人", "纪念日", "惊喜",
    "浪漫", "暧昧", "约她", "约他", "升温", "老夫老妻",
    "二人世界", "约会", "初次约会"  # 新增关键词
]
```

2. **优化匹配逻辑**
```python
# 添加更细致的匹配规则
if "怕尴尬" in text or "第一次" in text:
    understanding.relationship_stage = "暧昧/追求中"
if "纪念日" in text or "周年" in text:
    understanding.relationship_stage = "纪念日"
```

---

### 改进 2: 调整主题评分权重

**目标**: 让更匹配的主题排在前面

**文件**: `activity_agent/modules/theme_planner.py`

**代码位置**: 第 277-314 行 `_score_*()` 方法

**改进步骤**:

1. **杭州主题评分调整** (第 277-291 行)
```python
def _score_hangzhou(self, theme: Theme, request: UserRequest) -> int:
    request_tags = set([*request.experience_tags, *request.mood_tags])
    score = 10 * len(set(theme.trigger_tags) & request_tags)  # 提高权重 5→10
    score += 8 * len(set(theme.experience_tags) & request_tags)  # 提高权重 4→8
    # ... 其他调整
    return score
```

2. **情侣主题评分调整** (第 303-314 行)
```python
def _score_couple(self, theme: Theme, request: UserRequest) -> int:
    score = 0
    if request.relationship_stage in theme.stages:
        score += 8  # 提高权重 4→8
    if request.relationship_goal in theme.goals:
        score += 8  # 提高权重 4→8
    # ... 其他调整
    return score
```

---

### 改进 3: 更新主题定义

**目标**: 扩展主题标签，提升匹配覆盖度

**文件**: `activity_agent/modules/theme_planner.py`

**代码位置**: 第 6-245 行 主题定义区域

**改进步骤**:

1. **为现有主题添加更多标签**
```python
# 例子：下班回血局 (第 6-18 行)
Theme(
    id="friends_recovery",
    name="下班回血局",
    trigger_tags=["回血", "养生", "放松", "解压", "减压", "累"],  # 添加更多标签
    # ...
),
```

2. **增强杭州主题识别**
```python
# 杭州老城烟火半日局 (第 70-89 行)
Theme(
    id="hz_old_town_fireworks",
    trigger_tags=["杭州", "老城烟火", "特色美食", "本土底蕴", "低费脑",
                  "河坊街", "南宋御街", "杭州小吃", "吴山"],  # 添加具体地点标签
    # ...
),
```

---

### 改进 4: 优化 LLM Prompt

**目标**: 提高 LLM 理解的准确率

**文件**: `activity_agent/modules/dialogue_manager.py`

**代码位置**: 第 104-133 行 `system_prompt`

**改进步骤**:

1. **增强 Prompt 示例**
```python
system_prompt = """你是一个活动规划助手...

示例：
用户说："想约暧昧对象出去，怕尴尬" → scene: "couple", relationship_stage: "暧昧/追求中"
用户说："和哥们几个出去放松一下" → scene: "friends", mood_tags: ["放松", "热闹"]
用户说："去杭州西湖逛逛" → location: "西湖", mood_tags: ["出片", "放松"]

注意：
- 如果用户提到"怕尴尬"、"约她"、"约他"、"第一次"，relationship_stage很可能是"暧昧/追求中"
- 如果用户提到"纪念日"、"惊喜"、"浪漫"，scene很可能是"couple"
- 如果用户提到"杭州"、"西湖"、"运河"，应该优先考虑杭州主题
...
"""
```

---

## 📦 扩展新主题

### 完整步骤：添加一个新主题

#### 1️⃣ 在 `theme_planner.py` 中定义新主题

```python
# 在对应主题列表中添加
FRIENDS_THEMES: list[Theme] = [
    # ... 现有主题 ...
    Theme(
        id="friends_new_theme",
        name="我的新主题名字",
        emotional_hook="吸引人的文案描述",
        trigger_tags=["关键词1", "关键词2", "关键词3"],
        slots=[
            ThemeSlot(TimelineType.ACTIVITY, ["标签1", "标签2"], "描述"),
            ThemeSlot(TimelineType.DINING, ["标签1", "标签2"], "描述"),
            ThemeSlot(TimelineType.RELAX, ["标签1", "标签2"], "描述"),
        ],
        add_ons=["附加项1", "附加项2"],
    ),
]
```

#### 2️⃣ 在 `theme_keyword_seeds.py` 中添加关键词

```python
FRIENDS_THEME_KEYWORD_SEEDS: dict[str, list[str]] = {
    # ... 现有主题 ...
    "我的新主题名字": ["关键词1", "关键词2", "关键词3"],
    "friends_new_theme": ["关键词1", "关键词2", "关键词3"],
}
```

#### 3️⃣ 添加测试用例

在 `tests/theme_confirmation_cases.py` 中添加：

```python
ThemeConfirmationCase(
    case_id="test_new_theme_001",
    title="新主题测试",
    category="新功能验证",
    description="测试新添加的主题能否正确识别",
    turns=[
        ThemeConfirmationTurn(message="用户触发新主题的话", scene_hint=Scene.FRIENDS),
    ],
    expected_scene=Scene.FRIENDS,
    expected_top_theme_key="friends_new_theme",
    notes="验证新主题是否正常工作",
),
```

#### 4️⃣ 运行测试验证

```bash
python -m tests.run_mock_theme_confirmation
```

---

## 💡 完整示例

### 案例：修复"发疯解压局"识别问题

#### 问题描述
用户说"想好好疯一下"但没有推荐"发疯解压局"

#### 步骤 1: 分析当前逻辑
检查 `theme_planner.py`:
```python
# 第 43-54 行 - 发疯解压局定义
Theme(
    id="friends_release",
    name="发疯解压局",
    trigger_tags=["发疯", "解压"],  # 关键词太少！
    ...
),

# 第 293-301 行 - 朋友评分
def _score_friends(self, theme: Theme, request: UserRequest) -> int:
    score = 3 * len(set(theme.trigger_tags) & set(request.mood_tags))
    # 权重 3 可能不够高！
    ...
```

检查 `dialogue_manager.py`:
```python
# 规则解析中可能缺少相关关键词！
```

#### 步骤 2: 修复代码

**修复 1**: 增强主题标签
```python
# activity_agent/modules/theme_planner.py
Theme(
    id="friends_release",
    name="发疯解压局",
    trigger_tags=["发疯", "解压", "疯玩", "释放", "打拳", "发泄", "减压", "放松", "KTV"],  # 扩展
    ...
),
```

**修复 2**: 提高评分权重
```python
def _score_friends(self, theme: Theme, request: UserRequest) -> int:
    score = 5 * len(set(theme.trigger_tags) & set(request.mood_tags))  # 3→5
    ...
```

**修复 3**: 增强规则解析关键词
```python
# activity_agent/modules/dialogue_manager.py
# 在 _understand_with_rules() 的情绪标签部分
mood_keywords = {
    "解压": ["解压", "放松", "释放", "疯玩", "发泄", "发疯", "减压"],
    ...
}
```

#### 步骤 3: 测试验证
```bash
# 运行 Mock 模式测试
python -m tests.run_mock_theme_confirmation
# 查看报告是否改进
```

---

## 🎯 持续改进循环

1. **观察生产问题** → 收集用户反馈和错误案例
2. **添加测试用例** → 用 `tests/theme_confirmation_cases.py` 复现问题
3. **定位问题代码** → 使用本指南的定位方法
4. **修复代码** → 应用改进指南
5. **验证效果** → 运行测试看通过率提升
6. **部署更新** → 把改进推向生产

---

## 📞 需要帮助？

如果遇到问题：
1. 检查测试报告中的详细日志
2. 查看控制台输出的调试信息
3. 参考现有代码的模式
4. 运行 `demo_conversational.py` 进行交互式测试

---

**文档版本**: 1.0
**最后更新**: 2026-06-07
