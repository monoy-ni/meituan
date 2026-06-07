# 08 mock 美团预约与下单验收

## 目标

验证系统会通过 mock 美团 API 创建预约草稿、库存 hold、AA 草稿和确认订单，同时保持“用户确认前不支付、不下不可逆订单”的安全边界。

## 覆盖点

- 预约草稿创建前检查每个商户可用性
- 创建 booking hold
- 朋友局 AA 预付模式会创建 AA draft
- 用户取消时不产生订单
- 用户确认后产生 mock order/reservation IDs
- tool events 可追踪 mock 美团调用

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_08_mock_booking_order
```
