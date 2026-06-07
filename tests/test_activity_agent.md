# test_activity_agent.py 测试说明

## 1. 文件定位

对应测试代码：

- [test_activity_agent.py](test_activity_agent.py)

这个文件是整个 `ActivityPlanningAgent` 的核心业务流程测试，覆盖从“生成方案”到“反馈收敛、改方案、预约草稿、复盘总结”的主链路。

## 2. 主要覆盖内容

本文件重点验证：

1. 朋友局模糊输入能否生成 3 个候选方案
2. 邀请反馈能否收敛预算、迟到、不喝酒等约束
3. 基于上一轮请求的“便宜点、不喝酒”调整是否生效
4. 情侣场景是否生成低压力、不含酒店的安全约会方案
5. 预约草稿是否坚持“确认前不支付”
6. 活动结束后是否生成复盘结果和下次建议

## 3. 关键测试点

### `test_sparse_friends_request_generates_three_theme_options`

- 验证朋友局模糊输入可以生成 3 个备选方案
- 验证每个方案都有时间线
- 验证分享卡能正常生成

### `test_feedback_resolves_budget_late_arrival_and_no_alcohol`

- 验证多人反馈会影响预算和硬约束
- 验证“晚到”和“不喝酒”会进入新的请求与方案

### `test_adjust_request_can_make_plan_cheaper_and_no_alcohol`

- 验证基于历史请求的再规划能力
- 验证预算下降和禁酒限制会同步更新

### `test_couple_pursuit_outputs_low_pressure_date`

- 验证系统能识别情侣/暧昧场景
- 验证不会冒进安排酒店

### `test_booking_draft_requires_confirmation_before_payment`

- 验证预约草稿默认是待确认状态
- 验证不会在用户确认前自动支付

### `test_after_action_review_generates_memory_and_next_recommendations`

- 验证复盘数据可正常生成
- 验证会产出最佳环节和下次推荐

## 4. 测试价值

这个文件最像“主流程冒烟测试”，用于保证 Agent 的核心体验没有回归：

- 能规划
- 能调整
- 能预约
- 能复盘

如果这个文件失败，通常说明主业务流程发生了明显回归。

## 5. 运行方式

在项目根目录执行：

```powershell
python -m unittest tests.test_activity_agent
```

## 6. 通过标准

通过标准包括：

1. 所有测试通过
2. 朋友局/情侣局都能正常生成方案
3. 反馈与调整能真正改变请求结果
4. 预约仍然保留确认前安全边界
