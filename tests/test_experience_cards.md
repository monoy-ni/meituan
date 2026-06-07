# test_experience_cards.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_experience_cards.py](test_experience_cards.py)

这个文件主要验证“体验卡 / 玩法卡”相关能力，确保 Agent 在生成路线后，还能输出结构化的体验卡内容，并且在预约前保持安全边界。

## 2. 主要覆盖内容

本文件重点验证：

1. 朋友局能否生成 `themed-outing-designer` 风格体验卡
2. 情侣局能否生成 `couple-date-designer` 风格体验卡
3. 纪念日约会是否使用更强的仪式感语言
4. LLM 幻觉出的商户 ID 是否会被过滤
5. 创建预约草稿前是否先补齐体验卡
6. 后端接口层是否把 `experience_card` 正确暴露给前端

## 3. 关键测试点

### `test_friends_plan_includes_themed_outing_card`

- 验证朋友局生成的体验卡设计器名称正确
- 验证标题、玩法、流程、提示语等字段存在

### `test_couple_warmup_card_is_low_pressure_and_no_hotel`

- 验证暧昧/追求期的体验卡语气偏低压力、安全感
- 验证路线里默认不安排酒店

### `test_couple_anniversary_card_uses_ritual_language`

- 验证纪念日场景下，体验卡包含“仪式感”表达

### `test_designer_rejects_llm_hallucinated_merchant_ids`

- 验证即使 LLM 生成了不存在的商户 ID
- 系统也只保留真实候选商户

### `test_booking_guard_generates_card_before_mock_meituan_calls`

- 验证体验卡生成发生在预约工具调用之前
- 验证不会跳过玩法说明直接进入预约

### `test_backend_option_payload_exposes_experience_card`

- 验证后端序列化时会把体验卡字段带给前端

## 4. 测试价值

这个文件保证的不只是“有卡片”，而是：

- 卡片内容场景正确
- 卡片不会引用不存在的商户
- 卡片与预约链路先后顺序合理
- 前端可以拿到完整展示数据

它更偏向“规划结果可展示性”和“安全兜底”验证。

## 5. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_experience_cards
```

## 6. 通过标准

通过标准包括：

1. 朋友局和情侣局都能生成体验卡
2. 幻觉商户不会进入最终卡片
3. 预约草稿前会先补玩法卡
4. 接口返回中包含 `experience_card`
