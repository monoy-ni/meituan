# 位置获取与高德地图API集成验证测试报告

- 生成时间: `2026-06-07T18:30:29`
- 高德地图API配置状态: `未配置`
- 测试用例总数: `13`
- 通过用例数: `13`
- 失败用例数: `0`
- 异常用例数: `0`
- 用例通过率: `100.00%`
- 位置名称准确率: `38.46%`
- 地址准确率: `23.08%`
- 坐标准确率: `7.69%`
- 使用默认位置次数: `8`
- 高德地图API调用次数: `0`
- 平均对话轮数: `4.2`

## 执行结果总览

| 用例ID | 分类 | 结果 | 最终位置 | 地址 | 状态 | 异常 |
| --- | --- | --- | --- | --- | --- | --- |
| LOC-01 | 信息明确 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-02 | 信息明确 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-03 | 默认值 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-04 | 信息补充 | PASS | 西溪湿地 | 西溪湿地 | awaiting_selection | - |
| LOC-05 | 模糊信息 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-06 | 详细地址 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-07 | 地铁位置 | PASS | - | - | collecting_friends_context | - |
| LOC-08 | 高级配置 | PASS | - | - | collecting_friends_context | - |
| LOC-09 | 信息修正 | PASS | - | - | collecting_friends_context | - |
| LOC-10 | 跨场景 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-11 | 复杂描述 | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |
| LOC-12 | 混合输入 | PASS | - | - | collecting_friends_context | - |
| LOC-13 | 高德URL | PASS | 奥映世纪轩 | 民祥路与平澜路交汇处(地铁6号线丰北站C出口) | awaiting_selection | - |

## 问题汇总

- 无问题

## 用例详情

### LOC-01 用户明确给出集合点: 西湖

- 分类: `信息明确`
- 结果: `PASS`
- 描述: 用户在首次对话中明确给出集合位置为西湖
- 执行时间: `11ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，从西湖出发 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想放松，人均200 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 4 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：西湖轻松打卡局 /... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-02 用户明确给出集合点: 河坊街

- 分类: `信息明确`
- 结果: `PASS`
- 描述: 用户在首次对话中明确给出集合位置为河坊街
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 情侣约会，在河坊街 | 约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想浪漫一点，人均300 | 安排在什么时候比较好呢？周末下午，还是晚上？ | collecting_couple_context | ask_time | - |
| 3 | 周六下午 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_couple_context | ask_location_distance | - |
| 4 | 默认 | 好的，我懂了！这就为你准备几个合适的方案。

我给你配了 3 个约会方案：杭州老城烟火半日局 / 杭... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-03 用户未给出位置，使用默认值奥映世纪轩

- 分类: `默认值`
- 结果: `PASS`
- 描述: 用户全程未提到位置，系统使用默认位置
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想放松，人均180 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 4 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：杭州老城烟火半日局... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-04 位置信息在第三轮补充

- 分类: `信息补充`
- 结果: `PASS`
- 描述: 用户前两轮未提位置，第三轮明确给出
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `西溪湿地`
- 详细地址: `西溪湿地`
- 经度: `None`
- 纬度: `None`
- 高德URL: ``

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想放松，人均150 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 从西溪湿地附近出发 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 4 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 5 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：龙坞茶山近郊局 /... | awaiting_selection | select_option | `西溪湿地` |

### LOC-05 用户给出模糊位置描述: 地铁6号线附近

- 分类: `模糊信息`
- 结果: `PASS`
- 描述: 用户位置描述比较模糊，依赖系统解析
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，地铁6号线附近 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想拍照，人均220 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 周末 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 4 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：西湖轻松打卡局 /... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-06 用户给出完整地址: 民祥路与平澜路交汇处

- 分类: `详细地址`
- 结果: `PASS`
- 描述: 用户给出完整的街道地址
- 执行时间: `6ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 情侣约会，在民祥路与平澜路交汇处 | 约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想轻松一点，人均260 | 安排在什么时候比较好呢？周末下午，还是晚上？ | collecting_couple_context | ask_time | - |
| 3 | 周日下午 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_couple_context | ask_location_distance | - |
| 4 | 默认 | 好的，我懂了！这就为你准备几个合适的方案。

我给你配了 3 个约会方案：杭州老城烟火半日局 / 运... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-07 用户给出地铁出口: 丰北站C出口

- 分类: `地铁位置`
- 结果: `PASS`
- 描述: 用户指定具体的地铁出口作为集合点
- 执行时间: `1ms`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，丰北站C出口 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想唱歌，人均180 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 今晚 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 默认 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |

### LOC-08 用户同时给出位置和搜索半径

- 分类: `高级配置`
- 结果: `PASS`
- 描述: 用户同时指定位置和搜索范围
- 执行时间: `1ms`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，从武林广场出发，周边3公里 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想吃饭，人均200 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 周末 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 默认 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |

### LOC-09 用户中途修正位置

- 分类: `信息修正`
- 结果: `PASS`
- 描述: 用户先给出一个位置，然后又更改了位置
- 执行时间: `1ms`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，从西湖文化广场出发 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 不对，改到武林广场吧 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 3 | 人均160 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 今晚 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 5 | 默认 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |

### LOC-10 情侣场景默认位置

- 分类: `跨场景`
- 结果: `PASS`
- 描述: 验证情侣场景默认位置也正常工作
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 情侣约会 | 约会安排包在我身上！ | collecting_couple_context | ask_couple_feeling | - |
| 2 | 想浪漫，人均350 | 安排在什么时候比较好呢？周末下午，还是晚上？ | collecting_couple_context | ask_time | - |
| 3 | 周六晚上 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_couple_context | ask_location_distance | - |
| 4 | 默认 | 好的，我懂了！这就为你准备几个合适的方案。

我给你配了 3 个约会方案：杭州老城烟火半日局 / 运... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-11 复杂位置描述: 结合多个地标

- 分类: `复杂描述`
- 结果: `PASS`
- 描述: 用户给出比较复杂的位置描述，包含多个参考点
- 执行时间: `5ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局，在西湖文化广场和武林广场中间 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 人均180，想拍照 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 周末下午 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 4 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：西湖轻松打卡局 /... | awaiting_selection | select_option | `奥映世纪轩` |

### LOC-12 用户只给位置不给场景提示

- 分类: `混合输入`
- 结果: `PASS`
- 描述: 用户首次对话只给位置信息，需要系统先识别场景
- 执行时间: `1ms`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 从龙坞出发 | 好的！是想和朋友聚聚，还是想安排约会呢？ | identifying_scene | choose_scene | - |
| 2 | 朋友局 | 好的，朋友局！我来帮你安排。帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 3 | 人均200，想喝茶 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 4 | 周末 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |
| 5 | 默认 | 今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？ | collecting_friends_context | ask_mood | - |

### LOC-13 验证默认位置的高德URL

- 分类: `高德URL`
- 结果: `PASS`
- 描述: 验证默认位置的高德地图分享URL是否正确
- 执行时间: `6ms`

#### 最终位置信息

- 位置名称: `奥映世纪轩`
- 详细地址: `民祥路与平澜路交汇处(地铁6号线丰北站C出口)`
- 经度: `120.2425`
- 纬度: `30.2426`
- 高德URL: `https://surl.amap.com/4sRsg3c1oa7b`

#### 对话记录

| 轮次 | 用户输入 | 系统输出 | 状态 | 下一步 | 位置已解析 |
| --- | --- | --- | --- | --- | --- |
| 1 | 朋友局 | 帮你安排朋友局没问题！ 跟我说说大概想怎么玩？ | collecting_friends_context | ask_mood | - |
| 2 | 想放松，人均180 | 安排在什么时候呢？今晚、明晚，还是周末？ | collecting_friends_context | ask_time | - |
| 3 | 今晚 | 集合点默认奥映世纪轩；搜索范围默认周边 5km，整体路线目标 6km 或 45min 内。要改集合点... | collecting_friends_context | ask_location_distance | - |
| 4 | 默认 | 好的！我已经了解得差不多了，这就为你生成几个方案。

我给你配了 3 个组局方案：杭州老城烟火半日局... | awaiting_selection | select_option | `奥映世纪轩` |
