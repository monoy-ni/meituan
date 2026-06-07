# 主题确认功能验证测试报告

- 生成时间: `2026-06-07T21:09:36`
- 主题参考定义文件: `D:\meituan agent\activity_agent\data\theme_keyword_seeds.py`
- 测试用例总数: `10`
- 通过用例数: `0`
- 失败用例数: `10`
- 用例通过率: `0.00%`
- 主题定位准确率: `0.00%`
- 关系阶段定位准确率: `0.00%`
- 异常用例数: `10`
- 平均对话轮数: `3.0`

## 执行结果总览

| 用例ID | 分类 | 结果 | 最终主题 | 关系阶段 | 状态 | 异常 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-01 | 信息明确 | FAIL | - | - | collecting_friends_context | DialogueTurnTimeoutError |
| TC-02 | 信息明确 | FAIL | - | - | - | TypeError |
| TC-03 | 信息模糊 | FAIL | - | - | - | DialogueTurnTimeoutError |
| TC-04 | 信息明确 | FAIL | - | - | collecting_couple_context | TypeError |
| TC-05 | 信息明确 | FAIL | - | - | collecting_couple_context | TypeError |
| TC-06 | 边界场景 | FAIL | - | - | collecting_couple_context | TypeError |
| TC-07 | 信息完整 | FAIL | - | - | collecting_couple_context | DialogueTurnTimeoutError |
| TC-08 | 信息明确 | FAIL | - | - | collecting_friends_context | TypeError |
| TC-09 | 歧义信息 | FAIL | - | - | collecting_friends_context | DialogueTurnTimeoutError |
| TC-10 | 边界场景 | FAIL | - | - | collecting_friends_context | DialogueTurnTimeoutError |

## 问题汇总

- `TC-01` 朋友回血主题识别: DialogueTurnTimeoutError - Turn timed out after 20.00s: 默认
- `TC-02` 朋友出片聊天主题识别: TypeError - argument of type 'NoneType' is not iterable
- `TC-03` 模糊开场后确认省钱朋友局: DialogueTurnTimeoutError - Turn timed out after 20.00s: 今晚想出去玩
- `TC-04` 情侣暧昧升温主题识别: TypeError - unhashable type: 'list'
- `TC-05` 纪念日主题识别: TypeError - unhashable type: 'list'
- `TC-06` 关系修复主题识别: TypeError - unhashable type: 'list'
- `TC-07` 夜宿放松主题识别: DialogueTurnTimeoutError - Turn timed out after 20.00s: 人均700
- `TC-08` 杭州西湖低体力主题识别: TypeError - unhashable type: 'list'
- `TC-09` 雨天室内低耗主题识别: DialogueTurnTimeoutError - Turn timed out after 20.00s: 默认
- `TC-10` 发疯解压主题识别: DialogueTurnTimeoutError - Turn timed out after 20.00s: 默认

## TC-01 朋友回血主题识别

- 分类: `信息明确`
- 结果: `FAIL`
- 主题参考依据: `friends_recovery -> aliases=['friends_recovery', '下班兄弟回血局', '下班回血局'], keywords=['KTV', '烧烤', '酒吧']`
- 最终定位: `scene=friends` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | friends | friends | - |
| top_theme | FAIL | 下班回血局 | None | friends_recovery -> aliases=['friends_recovery', '下班兄弟回血局', '下班回血局'], keywords=['KTV', '烧烤', '酒吧'] |
| final_state | FAIL | awaiting_selection | collecting_friends_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 最近有点累，想放松回血 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 人均220 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - |

### 异常信息

- 类型: `DialogueTurnTimeoutError`
- 信息: `Turn timed out after 20.00s: 默认`

## TC-02 朋友出片聊天主题识别

- 分类: `信息明确`
- 结果: `FAIL`
- 主题参考依据: `friends_photo_chat -> aliases=['friends_photo_chat', '出片聊天局'], keywords=['展览', '甜品', '咖啡']`
- 最终定位: `scene=None` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | FAIL | friends | None | - |
| top_theme | FAIL | 出片聊天局 | None | friends_photo_chat -> aliases=['friends_photo_chat', '出片聊天局'], keywords=['展览', '甜品', '咖啡'] |
| final_state | FAIL | awaiting_selection | None | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |

### 异常信息

- 类型: `TypeError`
- 信息: `argument of type 'NoneType' is not iterable`

## TC-03 模糊开场后确认省钱朋友局

- 分类: `信息模糊`
- 结果: `FAIL`
- 主题参考依据: `friends_budget -> aliases=['friends_budget', '低成本快乐局'], keywords=['小吃', '桌游', '夜宵']`
- 最终定位: `scene=None` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | FAIL | friends | None | - |
| top_theme | FAIL | 低成本快乐局 | None | friends_budget -> aliases=['friends_budget', '低成本快乐局'], keywords=['小吃', '桌游', '夜宵'] |
| final_state | FAIL | awaiting_selection | None | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |

### 异常信息

- 类型: `DialogueTurnTimeoutError`
- 信息: `Turn timed out after 20.00s: 今晚想出去玩`

## TC-04 情侣暧昧升温主题识别

- 分类: `信息明确`
- 结果: `FAIL`
- 主题参考依据: `couple_warmup -> aliases=['couple_warmup', '轻升温不尴尬约会'], keywords=['手作', '甜品', '咖啡']`
- 最终定位: `scene=couple` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | couple | couple | - |
| relationship_stage | FAIL | 暧昧/追求中 | None | - |
| top_theme | FAIL | 轻升温不尴尬约会 | None | couple_warmup -> aliases=['couple_warmup', '轻升温不尴尬约会'], keywords=['手作', '甜品', '咖啡'] |
| final_state | FAIL | awaiting_selection | collecting_couple_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 情侣约会 | 约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想约她出来，有点怕尴尬，想自然一点 | 人均预算大概多少呢？我可以根据预算调整推荐。 | collecting_couple_context | ask_budget | - |
| 3 | 人均300 | 人均预算大概多少呢？我可以根据预算调整推荐。 | collecting_couple_context | ask_budget | - |
| 4 | 周六下午 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_couple_context | ask_location_distance | - |

### 异常信息

- 类型: `TypeError`
- 信息: `unhashable type: 'list'`

## TC-05 纪念日主题识别

- 分类: `信息明确`
- 结果: `FAIL`
- 主题参考依据: `couple_memory -> aliases=['couple_memory', '把普通周末过成小纪念日'], keywords=['手作', '西餐', '花店']`
- 最终定位: `scene=couple` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | couple | couple | - |
| relationship_stage | FAIL | 纪念日 | None | - |
| top_theme | FAIL | 把普通周末过成小纪念日 | None | couple_memory -> aliases=['couple_memory', '把普通周末过成小纪念日'], keywords=['手作', '西餐', '花店'] |
| final_state | FAIL | awaiting_selection | collecting_couple_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 纪念日想安排一下 | 约会安排包在我身上！ 纪念日要好好安排一下，给你准备点有仪式感的！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想浪漫一点，有点仪式感 | 人均预算大概多少呢？我可以根据预算调整推荐。 | collecting_couple_context | ask_budget | - |
| 3 | 人均520 | 安排在什么时候比较好呢？周末下午，还是晚上？ | collecting_couple_context | ask_time | - |
| 4 | 周末晚上 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_couple_context | ask_location_distance | - |

### 异常信息

- 类型: `TypeError`
- 信息: `unhashable type: 'list'`

## TC-06 关系修复主题识别

- 分类: `边界场景`
- 结果: `FAIL`
- 主题参考依据: `couple_repair -> aliases=['couple_repair', '关系修复缓冲约会'], keywords=['茶馆', '安静餐厅', '散步']`
- 最终定位: `scene=couple` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | couple | couple | - |
| relationship_stage | FAIL | 想修复关系 | None | - |
| top_theme | FAIL | 关系修复缓冲约会 | None | couple_repair -> aliases=['couple_repair', '关系修复缓冲约会'], keywords=['茶馆', '安静餐厅', '散步'] |
| final_state | FAIL | awaiting_selection | collecting_couple_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 最近跟对象吵架了，想修复关系 | 好的！是想和朋友聚聚，还是想安排约会呢？ | identifying_scene | choose_scene | - |
| 2 | 想找个安静点的地方缓和一下 | 好的，约会安排！约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 3 | 人均280 | 安排在什么时候比较好呢？周末下午，还是晚上？ | collecting_couple_context | ask_time | - |
| 4 | 周末 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_couple_context | ask_location_distance | - |

### 异常信息

- 类型: `TypeError`
- 信息: `unhashable type: 'list'`

## TC-07 夜宿放松主题识别

- 分类: `信息完整`
- 结果: `FAIL`
- 主题参考依据: `couple_overnight -> aliases=['couple_overnight', '夜宿放松约会'], keywords=['手作', '西餐', '酒店']`
- 最终定位: `scene=couple` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | couple | couple | - |
| relationship_stage | FAIL | 稳定情侣 | None | - |
| top_theme | FAIL | 夜宿放松约会 | None | couple_overnight -> aliases=['couple_overnight', '夜宿放松约会'], keywords=['手作', '西餐', '酒店'] |
| final_state | FAIL | awaiting_selection | collecting_couple_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 情侣约会 | 约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想过夜放松，酒店也可以 | 人均预算大概多少呢？我可以根据预算调整推荐。 | collecting_couple_context | ask_budget | - |

### 异常信息

- 类型: `DialogueTurnTimeoutError`
- 信息: `Turn timed out after 20.00s: 人均700`

## TC-08 杭州西湖低体力主题识别

- 分类: `信息明确`
- 结果: `FAIL`
- 主题参考依据: `hz_westlake_easy -> aliases=['hz_westlake_easy', '西湖轻松打卡局'], keywords=['茶馆', '咖啡', '西湖景点']`
- 最终定位: `scene=friends` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | friends | friends | - |
| top_theme | FAIL | 西湖轻松打卡局 | None | hz_westlake_easy -> aliases=['hz_westlake_easy', '西湖轻松打卡局'], keywords=['茶馆', '咖啡', '西湖景点'] |
| final_state | FAIL | awaiting_selection | collecting_friends_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想杭州本地探索，去西湖打卡，少走路一点 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 人均180 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 周末下午 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - |

### 异常信息

- 类型: `TypeError`
- 信息: `unhashable type: 'list'`

## TC-09 雨天室内低耗主题识别

- 分类: `歧义信息`
- 结果: `FAIL`
- 主题参考依据: `hz_rainy_indoor -> aliases=['hz_rainy_indoor', '雨天室内低耗局'], keywords=['商场', '手作', '茶馆']`
- 最终定位: `scene=friends` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | friends | friends | - |
| top_theme | FAIL | 雨天室内低耗局 | None | hz_rainy_indoor -> aliases=['hz_rainy_indoor', '雨天室内低耗局'], keywords=['商场', '手作', '茶馆'] |
| final_state | FAIL | awaiting_selection | collecting_friends_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 和朋友出去玩 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 下雨天也想找个室内地方，不想太累 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 人均160 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 4 | 周末 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - |

### 异常信息

- 类型: `DialogueTurnTimeoutError`
- 信息: `Turn timed out after 20.00s: 默认`

## TC-10 发疯解压主题识别

- 分类: `边界场景`
- 结果: `FAIL`
- 主题参考依据: `friends_release -> aliases=['friends_release', '发疯解压局'], keywords=['KTV', '拳击', '酒吧', '烧烤']`
- 最终定位: `scene=friends` / `relationship_stage=None` / `top_theme=None`

### 校验明细

| 校验项 | 结果 | 预期 | 实际 | 说明 |
| --- | --- | --- | --- | --- |
| scene | PASS | friends | friends | - |
| top_theme | FAIL | 发疯解压局 | None | friends_release -> aliases=['friends_release', '发疯解压局'], keywords=['KTV', '拳击', '酒吧', '烧烤'] |
| final_state | FAIL | awaiting_selection | collecting_friends_context | - |
| options_count | FAIL | >=3 | 0 | - |

### 对话转录

| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 最近压力太大了，想发疯解压，热闹一点 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 人均260 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 4 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点、距离或路线长度吗？ | collecting_friends_context | ask_location_distance | - |

### 异常信息

- 类型: `DialogueTurnTimeoutError`
- 信息: `Turn timed out after 20.00s: 默认`
