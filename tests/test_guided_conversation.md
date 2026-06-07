# test_guided_conversation.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_guided_conversation.py](test_guided_conversation.py)

这个文件主要测试“多轮引导式对话”能力，验证 Agent 是否能通过连续聊天逐步收集上下文，并在条件足够时自动产出方案。

## 2. 主要覆盖内容

本文件重点验证：

1. 朋友局引导过程中是否先收集信息、后出卡片
2. 情侣局能否在不直接追问关系阶段的情况下推断关系状态
3. 多轮对话中用户追加“便宜点、少走路”后是否能原地重生成方案
4. 多轮引导下的预约草稿和确认是否安全
5. 后端 `guided_chat` 接口是否返回对话状态元数据
6. 自定义出发地、搜索半径、路线限制是否能在引导中被接收

## 3. 关键测试点

### `test_guided_friends_collects_context_before_cards`

- 验证朋友局多轮收集预算、时间、情绪后才出方案
- 验证默认集合点和默认半径会写入请求

### `test_guided_couple_infers_relationship_without_direct_question`

- 验证系统能从上下文推断“暧昧/追求中”
- 验证不会机械地把关系阶段选项原样抛给用户

### `test_guided_adjustment_regenerates_options_same_turn`

- 验证在已经生成方案后，继续一句“便宜点，少走路”可以立即重规划

### `test_booking_stays_draft_until_user_confirmation`

- 验证引导式对话下的预约流程仍保持草稿、取消、确认三步

### `test_guided_api_returns_conversation_metadata`

- 验证接口层能返回 `scene`、`state`、`next_step` 等对话状态信息

### `test_guided_context_accepts_custom_location_and_distance`

- 验证用户自定义地点、3 公里范围、4 公里路线、40 分钟限制可被正确提取

## 4. 测试价值

这个文件的价值在于验证“对话式收集需求”是否稳定。

它不是单次 `plan()` 的测试，而是多轮状态机测试，能帮助发现：

- 对话状态切换错误
- 缺失信息收集不完整
- 对话式调整无法生效
- 接口层和 Agent 层状态不一致

## 5. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_guided_conversation
```

## 6. 通过标准

通过标准包括：

1. 多轮引导能最终生成 3 个方案
2. 请求中的预算、地点、半径、路线限制提取正确
3. 引导式调整可直接触发再规划
4. 对话状态元数据可供前端使用
