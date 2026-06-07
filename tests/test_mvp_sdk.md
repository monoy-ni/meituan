# test_mvp_sdk.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_mvp_sdk.py](file:///d:/meituan%20agent/tests/test_mvp_sdk.py)

这个文件主要测试 SDK 和基础设施层能力，覆盖环境变量加载、LLM 客户端选择、SQLite 持久化、跨实例恢复、反馈持久化和情侣局酒店/礼物草稿等内容。

## 2. 主要覆盖内容

本文件重点验证：

1. `AgentSettings.from_env()` 是否能正确读取环境变量
2. `OpenAICompatibleLLMClient` 在无 Key 时是否拒绝真实调用
3. 没有真实 LLM 时系统是否仍可运行
4. Session、方案、预约草稿是否能在重启 Agent 后继续使用
5. 提交反馈后，修正方案是否能持久化
6. 情侣局酒店和礼物是否能生成对应草稿项

## 3. 关键测试点

### `test_env_settings_load_openai_compatible_config`

- 验证环境变量能正确映射到设置对象

### `test_openai_client_requires_api_key_for_real_calls`

- 验证真实 OpenAI 兼容客户端在未配置 Key 时会报错

### `test_chat_works_without_llm`

- 验证仅使用 `MockLLMClient` 也能生成方案

### `test_session_persists_plans_and_booking_drafts_across_agent_instances`

- 验证 SQLite 持久化生效
- 验证重启 Agent 后还能继续创建 draft 和确认订单

### `test_submit_feedback_persists_revised_lower_budget_plan`

- 验证反馈调整后的方案会写入持久层

### `test_couple_hotel_and_gift_create_mock_hotel_and_delivery_drafts`

- 验证情侣纪念日场景会生成酒店与礼物相关草稿

## 4. 测试价值

这个文件主要验证“系统基础能力是否稳”。

它不是偏某个主题玩法，而是偏：

- 配置
- 持久化
- SDK 调用
- Agent 实例重启恢复
- 基础 booking 行为

如果这个文件失败，通常需要优先排查：

- 环境变量读取
- SQLite 存储
- LLM client 选择
- session 恢复和 draft 恢复

## 5. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_mvp_sdk
```

## 6. 通过标准

通过标准包括：

1. 环境变量加载正确
2. 无 LLM 也可运行
3. 跨实例数据可恢复
4. 反馈修正方案可以持久化
5. 情侣酒店/礼物草稿正常生成
